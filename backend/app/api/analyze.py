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
from app.models.analysis import Analysis
from app.models.resume import Resume
from app.models.job import Job

router = APIRouter(
    prefix="/analyze",
    tags=["analysis"],
)

@router.post(
    "",
    response_model=AnalyzeResponse,
)
async def analyze_resume_against_job(
    payload: AnalyzeRequest,
    db: Session = Depends(get_db),
):
    """
    Compare one resume against one job description.
    """

    resume_repo = ResumeRepository(db)
    job_repo = JobRepository(db)
    analysis_repo = AnalysisRepository(db)

    resume = resume_repo.get_by_id(payload.resume_id)

    if not resume:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "RESUME_NOT_FOUND",
                "message": "Resume not found.",
            },
        )

    job = job_repo.get_by_id(payload.job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "JOB_NOT_FOUND",
                "message": "Job not found.",
            },
        )

    # ------------------------------------------------------
    # 4. Check cached analysis based on content_hash logic
    #
    # We join Analysis to Resume and Job to explicitly check if ANY
    # prior analysis was done targeting the *exact same* raw_text
    # (represented by content_hash). If so, we reuse the result
    # instead of re-computing the deterministic arrays.
    # ------------------------------------------------------

    existing_analysis = (
        db.query(Analysis)
        .join(Resume, Analysis.resume_id == Resume.id)
        .join(Job, Analysis.job_id == Job.id)
        .filter(
            Resume.content_hash == resume.content_hash,
            Job.content_hash == job.content_hash
        )
        .order_by(Analysis.created_at.desc())
        .first()
    )

    if existing_analysis:
        return AnalyzeResponse(
            id=existing_analysis.id,
            resume_id=existing_analysis.resume_id,
            job_id=existing_analysis.job_id,
            overall_score=existing_analysis.overall_score or 0.0,
            skill_score=existing_analysis.skill_score or 0.0,
            semantic_score=existing_analysis.semantic_score or 0.0,
            experience_score=existing_analysis.experience_score or 0.0,
            education_score=existing_analysis.education_score or 0.0,
            project_evidence_score=(
                existing_analysis.project_evidence_score or 0.0
            ),
            matched_skills=existing_analysis.matched_skills or [],
            missing_skills=existing_analysis.missing_skills or [],
            related_skills=existing_analysis.related_skills or [],
            explanation=existing_analysis.explanation,
            cached=True
        )

    # ------------------------------------------------------
    # 5. Run Matching Engine
    # ------------------------------------------------------

    try:
        engine = MatchingEngine()

        result = engine.calculate_match(
            resume,
            job,
        )

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail={
                "code": "MATCHING_FAILED",
                "message": "Failed to calculate resume-job match.",
                "error": str(e),
            },
        ) from e


    analysis_data = {
        "overall_score": result["overall_score"],
        "skill_score": result["sub_scores"]["skill_score"],
        "semantic_score": result["sub_scores"]["semantic_score"],
        "experience_score": result["sub_scores"]["experience_score"],
        "education_score": result["sub_scores"]["education_score"],
        "project_evidence_score": (
            result["sub_scores"]["project_evidence_score"]
        ),
        "matched_skills": result["matched_skills"],
        "missing_skills": result["missing_skills"],
        "related_skills": result["related_skills"],
        "explanation": None,
    }

    analysis = analysis_repo.create(
        session_id=resume.session_id,
        resume_id=resume.id,
        job_id=job.id,
        analysis_data=analysis_data,
    )

    return AnalyzeResponse(
        id=analysis.id,
        resume_id=analysis.resume_id,
        job_id=analysis.job_id,
        overall_score=analysis.overall_score or 0.0,
        skill_score=analysis.skill_score or 0.0,
        semantic_score=analysis.semantic_score or 0.0,
        experience_score=analysis.experience_score or 0.0,
        education_score=analysis.education_score or 0.0,
        project_evidence_score=(
            analysis.project_evidence_score or 0.0
        ),
        matched_skills=analysis.matched_skills or [],
        missing_skills=analysis.missing_skills or [],
        related_skills=result.get("related_skills", []),
        explanation=analysis.explanation,
        cached=False
    )
