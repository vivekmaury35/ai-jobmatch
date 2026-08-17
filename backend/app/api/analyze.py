import asyncio
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.base import ResumeRepository, JobRepository, AnalysisRepository
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from app.services.matching import MatchingEngine
from app.services.ai import AIService, AIExtractionError
from app.models.analysis import Analysis, Recommendation
from app.models.resume import Resume
from app.models.job import Job

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyze", tags=["analysis"])

@router.post("", response_model=AnalyzeResponse, status_code=200)
async def analyze_resume_against_job(payload: AnalyzeRequest, db: Session = Depends(get_db)):
    resume = ResumeRepository(db).get_by_id(payload.resume_id)
    job = JobRepository(db).get_by_id(payload.job_id)
    if not resume or not job: raise HTTPException(status_code=404, detail="Resume/Job not found")

    existing = (
        db.query(Analysis)
        .join(Resume, Analysis.resume_id == Resume.id)
        .join(Job, Analysis.job_id == Job.id)
        .filter(Resume.content_hash == resume.content_hash, Job.content_hash == job.content_hash)
        .order_by(Analysis.created_at.desc())
        .first()
    )

    if existing:
        recs = [{"type": r.type, "content": r.content, "priority": r.priority} for r in (existing.recommendations or [])]
        return AnalyzeResponse(id=existing.id, resume_id=existing.resume_id, job_id=existing.job_id, overall_score=existing.overall_score or 0.0, skill_score=existing.skill_score or 0.0, semantic_score=existing.semantic_score or 0.0, experience_score=existing.experience_score or 0.0, education_score=existing.education_score or 0.0, project_evidence_score=existing.project_evidence_score or 0.0, matched_skills=existing.matched_skills or [], missing_skills=existing.missing_skills or [], related_skills=existing.related_skills or [], explanation=existing.explanation, recommendations=recs, cached=True, created_at=existing.created_at)

    engine = MatchingEngine()
    match_result = await asyncio.to_thread(engine.calculate_match, resume, job)

    explanation_text, recommendations_raw = None, []
    try:
        explanation_result = await AIService().generate_explanation({
            "overall_score": match_result["overall_score"],
            "skill_score": match_result["sub_scores"]["skill_score"],
            "semantic_score": match_result["sub_scores"]["semantic_score"],
            "experience_score": match_result["sub_scores"]["experience_score"],
            "education_score": match_result["sub_scores"]["education_score"],
            "project_evidence_score": match_result["sub_scores"]["project_evidence_score"],
            "matched_skills": match_result["matched_skills"],
            "missing_skills": match_result["missing_skills"],
            "related_skills": match_result["related_skills"],
        })
        explanation_text = explanation_result.get("explanation")
        recommendations_raw = explanation_result.get("recommendations", [])
    except Exception as e:
        logger.warning("Explanation failed: %s", e)

    analysis = AnalysisRepository(db).create(session_id=resume.session_id, resume_id=resume.id, job_id=job.id, analysis_data={
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
    })

    for rec in recommendations_raw:
        db.add(Recommendation(analysis_id=analysis.id, **rec))
    db.commit()
    db.refresh(analysis)

    return AnalyzeResponse(id=analysis.id, resume_id=analysis.resume_id, job_id=analysis.job_id, overall_score=analysis.overall_score or 0.0, skill_score=analysis.skill_score or 0.0, semantic_score=analysis.semantic_score or 0.0, experience_score=analysis.experience_score or 0.0, education_score=analysis.education_score or 0.0, project_evidence_score=analysis.project_evidence_score or 0.0, matched_skills=analysis.matched_skills or [], missing_skills=analysis.missing_skills or [], related_skills=analysis.related_skills or [], explanation=analysis.explanation, recommendations=recommendations_raw, cached=False, created_at=analysis.created_at)

@router.get("", response_model=list[AnalyzeResponse])
async def list_analyses(db: Session = Depends(get_db)):
    analyses = db.query(Analysis).order_by(Analysis.created_at.desc()).all()
    results = []
    for analysis in analyses:
        recs = [{"type": r.type, "content": r.content, "priority": r.priority} for r in (analysis.recommendations or [])]
        results.append(AnalyzeResponse(id=analysis.id, resume_id=analysis.resume_id, job_id=analysis.job_id, overall_score=analysis.overall_score or 0.0, skill_score=analysis.skill_score or 0.0, semantic_score=analysis.semantic_score or 0.0, experience_score=analysis.experience_score or 0.0, education_score=analysis.education_score or 0.0, project_evidence_score=analysis.project_evidence_score or 0.0, matched_skills=analysis.matched_skills or [], missing_skills=analysis.missing_skills or [], related_skills=analysis.related_skills or [], explanation=analysis.explanation, recommendations=recs, created_at=analysis.created_at))
    return results

@router.get("/{analysis_id}", response_model=AnalyzeResponse)
async def get_analysis(analysis_id: UUID, db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis: raise HTTPException(status_code=404, detail="Analysis not found")
    recs = [{"type": r.type, "content": r.content, "priority": r.priority} for r in (analysis.recommendations or [])]
    return AnalyzeResponse(id=analysis.id, resume_id=analysis.resume_id, job_id=analysis.job_id, overall_score=analysis.overall_score or 0.0, skill_score=analysis.skill_score or 0.0, semantic_score=analysis.semantic_score or 0.0, experience_score=analysis.experience_score or 0.0, education_score=analysis.education_score or 0.0, project_evidence_score=analysis.project_evidence_score or 0.0, matched_skills=analysis.matched_skills or [], missing_skills=analysis.missing_skills or [], related_skills=analysis.related_skills or [], explanation=analysis.explanation, recommendations=recs, created_at=analysis.created_at)
