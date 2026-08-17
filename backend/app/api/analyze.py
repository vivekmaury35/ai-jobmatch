import asyncio
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.repositories.base import (
    ResumeRepository,
    JobRepository,
    AnalysisRepository,
)
from app.schemas.analysis import (
    AnalyzeRequest,
    AnalyzeResponse,
)
from app.services.matching import MatchingEngine
from app.services.ai import AIService, AIExtractionError
from app.models.analysis import Analysis, Recommendation
from app.models.resume import Resume
from app.models.job import Job

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/analyze",
    tags=["analysis"],
)


@router.post(
    "",
    response_model=AnalyzeResponse,
    status_code=200,
)
async def analyze_resume_against_job(
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Compare one resume against one job description.

    On cache miss, the matching engine (sync, CPU-bound) is dispatched to a
    thread via asyncio.to_thread so it doesn't block the event loop, then
    generate_explanation() fires as a standard async Gemini call. The
    two await points are sequential because explanation depends on match
    results, but neither blocks the event loop while waiting — other
    requests can be served during both waits.
    """

    resume_repo = ResumeRepository(db)
    job_repo = JobRepository(db)
    analysis_repo = AnalysisRepository(db)

    resume = resume_repo.get_by_id(payload.resume_id)
    if not resume:
        raise HTTPException(
            status_code=404,
            detail={"code": "RESUME_NOT_FOUND", "message": "Resume not found."},
        )

    job = job_repo.get_by_id(payload.job_id)
    if not job:
        raise HTTPException(
            status_code=404,
            detail={"code": "JOB_NOT_FOUND", "message": "Job not found."},
        )

    # ------------------------------------------------------------------
    # Cache check: if any prior analysis used the same raw content
    # (identified by content_hash) we return it instantly without
    # re-running matching or hitting Gemini again.
    # ------------------------------------------------------------------
    existing = (
        db.query(Analysis)
        .join(Resume, Analysis.resume_id == Resume.id)
        .join(Job, Analysis.job_id == Job.id)
        .filter(
            Resume.content_hash == resume.content_hash,
            Job.content_hash == job.content_hash,
        )
        .order_by(Analysis.created_at.desc())
        .first()
    )

    if existing:
        recommendations = [
            {"type": r.type, "content": r.content, "priority": r.priority}
            for r in (existing.recommendations or [])
        ]
        return AnalyzeResponse(
            id=existing.id,
            resume_id=existing.resume_id,
            job_id=existing.job_id,
            overall_score=existing.overall_score or 0.0,
            skill_score=existing.skill_score or 0.0,
            semantic_score=existing.semantic_score or 0.0,
            experience_score=existing.experience_score or 0.0,
            education_score=existing.education_score or 0.0,
            project_evidence_score=existing.project_evidence_score or 0.0,
            matched_skills=existing.matched_skills or [],
            missing_skills=existing.missing_skills or [],
            related_skills=existing.related_skills or [],
            explanation=existing.explanation,
            recommendations=recommendations,
            cached=True,
            created_at=existing.created_at,
        )

    # ------------------------------------------------------------------
    # Step 1: Run matching engine.
    #
    # MatchingEngine is synchronous (sentence-transformers + numpy — no
    # async support). asyncio.to_thread dispatches it to a worker thread so
    # the event loop stays free to handle other requests while it runs.
    # This is the correct way to call blocking code from an async endpoint.
    # ------------------------------------------------------------------
    try:
        engine = MatchingEngine()
        match_result = await asyncio.to_thread(engine.calculate_match, resume, job)
    except Exception as e:
        logger.exception("Matching engine failed")
        raise HTTPException(
            status_code=500,
            detail={"code": "MATCHING_FAILED", "message": "Failed to calculate match.", "error": str(e)},
        ) from e

    # ------------------------------------------------------------------
    # Step 2: Generate explanation via Gemini (async network call).
    #
    # This depends on match_result so it must run after Step 1.
    # It is a single async Gemini call — the event loop yields here,
    # allowing other requests to be served during the ~3-5s network wait.
    #
    # asyncio.gather() pattern: if we had TWO independent async calls
    # (e.g., concurrently generating an explanation AND a separate skill
    # gap analysis), gather would fire both simultaneously and collect
    # results when both finish — saving the wall-clock cost of the slower
    # one instead of paying sum(both). Here we have one call, so gather
    # would add no benefit; we await directly.
    # ------------------------------------------------------------------
    explanation_text = None
    recommendations_raw = []

    try:
        ai_service = AIService()
        explanation_context = {
            "overall_score": match_result["overall_score"],
            "skill_score": match_result["sub_scores"]["skill_score"],
            "semantic_score": match_result["sub_scores"]["semantic_score"],
            "experience_score": match_result["sub_scores"]["experience_score"],
            "education_score": match_result["sub_scores"]["education_score"],
            "project_evidence_score": match_result["sub_scores"]["project_evidence_score"],
            "matched_skills": match_result["matched_skills"],
            "missing_skills": match_result["missing_skills"],
            "related_skills": match_result["related_skills"],
        }
        explanation_result = await ai_service.generate_explanation(explanation_context)
        explanation_text = explanation_result.get("explanation")
        recommendations_raw = explanation_result.get("recommendations", [])

    except AIExtractionError as e:
        # Explanation failure is non-fatal: we still return the scores.
        # The frontend should handle explanation=null gracefully.
        logger.warning("Explanation generation failed (non-fatal): %s", e)
    except Exception as e:
        logger.exception("Unexpected error during explanation generation")

    # ------------------------------------------------------------------
    # Persist: Analysis row + Recommendation rows
    # ------------------------------------------------------------------
    try:
        analysis_data = {
            "overall_score": match_result["overall_score"],
            "skill_score": match_result["sub_scores"]["skill_score"],
            "semantic_score": match_result["sub_scores"]["semantic_score"],
            "experience_score": match_result["sub_scores"]["experience_score"],
            "education_score": match_result["sub_scores"]["education_score"],
            "project_evidence_score": match_result["sub_scores"]["project_evidence_score"],
            "matched_skills": match_result["matched_skills"],
            "missing_skills": match_result["missing_skills"],
            "related_skills": match_result["related_skills"],
            "explanation": explanation_text,
        }

        analysis = analysis_repo.create(
            session_id=resume.session_id,
            resume_id=resume.id,
            job_id=job.id,
            analysis_data=analysis_data,
        )

        # Persist recommendations as child rows
        for rec in recommendations_raw:
            db_rec = Recommendation(
                analysis_id=analysis.id,
                type=rec.get("type", "add_skill"),
                content=rec.get("content", ""),
                priority=int(rec.get("priority", 1)),
            )
            db.add(db_rec)
        db.commit()
        db.refresh(analysis)

    except Exception as e:
        db.rollback()
        logger.exception("Failed to persist analysis")
        raise HTTPException(
            status_code=500,
            detail={"code": "PERSISTENCE_FAILED", "message": "Failed to save analysis.", "error": str(e)},
        ) from e

    persisted_recommendations = [
        {"type": r.type, "content": r.content, "priority": r.priority}
        for r in (analysis.recommendations or [])
    ]

    return AnalyzeResponse(
        id=analysis.id,
        resume_id=analysis.resume_id,
        job_id=analysis.job_id,
        overall_score=analysis.overall_score or 0.0,
        skill_score=analysis.skill_score or 0.0,
        semantic_score=analysis.semantic_score or 0.0,
        experience_score=analysis.experience_score or 0.0,
        education_score=analysis.education_score or 0.0,
        project_evidence_score=analysis.project_evidence_score or 0.0,
        matched_skills=analysis.matched_skills or [],
        missing_skills=analysis.missing_skills or [],
        related_skills=analysis.related_skills or [],
        explanation=analysis.explanation,
        recommendations=persisted_recommendations,
        cached=False,
        created_at=analysis.created_at,
    )
