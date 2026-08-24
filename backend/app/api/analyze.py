import asyncio
import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.scoring_config import SCORING_VERSION
from app.repositories.base import ResumeRepository, JobRepository, AnalysisRepository
from app.schemas.analysis import AnalyzeRequest, AnalyzeResponse
from app.services.matching import MatchingEngine
from app.services.ai import AIService
from app.models.analysis import Analysis, Recommendation
from app.models.resume import Resume
from app.models.job import Job

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analyze", tags=["analysis"])

def build_analyze_response(analysis: Analysis, cached: bool = False, debug_info: dict | None = None) -> AnalyzeResponse:
    recs = [{"type": r.type, "content": r.content, "priority": r.priority} for r in (analysis.recommendations or [])]

    # `related_skills` is repurposed to store the certifications list, kept
    # separate from matched_skills/missing_skills per spec item 8.
    stored_related = analysis.related_skills or []
    certifications = stored_related if isinstance(stored_related, list) else []

    return AnalyzeResponse(
        id=analysis.id,
        resume_id=analysis.resume_id,
        job_id=analysis.job_id,
        job_title=analysis.job.title if analysis.job else None,
        confidence_tier=getattr(analysis, 'confidence_tier', None),
        tier_label=getattr(analysis, 'tier_label', None),
        tier_advice=getattr(analysis, 'tier_advice', None),
        overall_score=float(analysis.overall_score or 0.0),
        required_skills_matched=getattr(analysis, 'required_skills_matched', 0),
        required_skills_total=getattr(analysis, 'required_skills_total', 0),
        preferred_skills_matched=getattr(analysis, 'preferred_skills_matched', 0),
        preferred_skills_total=getattr(analysis, 'preferred_skills_total', 0),
        experience_years_candidate=float(getattr(analysis, 'experience_years_candidate', 0.0)),
        experience_years_required=float(getattr(analysis, 'experience_years_required', 0.0)),
        experience_gap_years=float(getattr(analysis, 'experience_gap_years', 0.0)),
        education_gate=getattr(analysis, 'education_gate', None),
        education_requirement=getattr(analysis, 'education_requirement', None),
        skill_score=float(analysis.skill_score or 0.0),
        experience_score=float(analysis.experience_score or 0.0),
        education_score=float(analysis.education_score or 0.0),
        project_evidence_score=float(analysis.project_evidence_score or 0.0),
        soft_skills_score=float(getattr(analysis, 'soft_skills_score', None) or 0.0),
        ai_tools_score=float(getattr(analysis, 'ai_tools_score', None) or 0.0),
        responsibilities_score=float(getattr(analysis, 'responsibilities_score', None) or 0.0),
        location_score=float(getattr(analysis, 'location_score', None) or 0.0),
        certification_score=float(getattr(analysis, 'certification_score', None) if getattr(analysis, 'certification_score', None) is not None else 100.0),
        matched_skills=analysis.matched_skills or [],
        missing_skills=analysis.missing_skills or [],
        related_skills=analysis.related_skills or [],
        certifications=certifications,
        explanation=analysis.explanation,
        recommendations=recs,
        cached=cached,
        created_at=analysis.created_at,
        debug_info=debug_info
    )

@router.post("", response_model=AnalyzeResponse, status_code=200)
async def analyze_resume_against_job(payload: AnalyzeRequest, response: Response, db: Session = Depends(get_db), debug: bool = False):
    resume = ResumeRepository(db).get_by_id(payload.resume_id)
    job = JobRepository(db).get_by_id(payload.job_id)
    if not resume or not job: raise HTTPException(status_code=404, detail="Resume/Job not found")

    # Keep the frontend's session in sync with the resume's actual owning session,
    # in case the client-side session id had drifted (e.g. cookie not round-tripped).
    response.headers["X-Session-ID"] = str(resume.session_id)
    response.set_cookie(key="session_id", value=str(resume.session_id), httponly=True, samesite="lax", max_age=30*24*60*60)

    cache_version = f"v{SCORING_VERSION}"

    existing = (
        db.query(Analysis)
        .join(Resume, Analysis.resume_id == Resume.id)
        .join(Job, Analysis.job_id == Job.id)
        .filter(
            Resume.content_hash == resume.content_hash,
            Job.content_hash == job.content_hash,
            # Only hit cache if it was generated with the current scoring logic version
            Analysis.scoring_version == cache_version if hasattr(Analysis, 'scoring_version') else True
        )
        .order_by(Analysis.created_at.desc())
        .first()
    )

    if existing and not debug:
        return build_analyze_response(existing, cached=True)

    engine = MatchingEngine()
    # Core LLM processing occurs here. Debug mode always forces a fresh
    # evaluation so the debug trace reflects the current pipeline/JD/resume.
    match_result = await engine.calculate_match_expert_llm(resume, job, debug=debug)

    if existing and debug:
        # Already cached - just return the cached record annotated with a
        # fresh debug trace instead of writing a duplicate analysis row.
        return build_analyze_response(existing, cached=True, debug_info=match_result.get("debug_info"))

    metrics = match_result.get("metrics", {})
    conf = match_result.get("confidence", {})

    analysis_data = {
        "overall_score": match_result["overall_score"],
        "skill_score": match_result["sub_scores"]["skill_score"],
        "experience_score": match_result["sub_scores"]["experience_score"],
        "education_score": match_result["sub_scores"]["education_score"],
        "project_evidence_score": match_result["sub_scores"]["project_evidence_score"],
        "soft_skills_score": match_result["sub_scores"]["soft_skills_score"],
        "ai_tools_score": match_result["sub_scores"]["ai_tools_score"],
        "responsibilities_score": match_result["sub_scores"]["responsibilities_score"],
        "location_score": match_result["sub_scores"]["location_score"],
        "certification_score": match_result["sub_scores"]["certification_score"],
        "matched_skills": match_result["matched_skills"],
        "missing_skills": match_result["missing_skills"],
        # `related_skills` is repurposed to store certifications, tracked
        # entirely separately from technical skills (spec item 8).
        "related_skills": match_result.get("certifications", []),
        "explanation": match_result.get("explanation"),
        "scoring_version": cache_version,

        # Confidence tier columns
        "confidence_tier": conf.get("tier"),
        "tier_label": conf.get("label"),
        "tier_advice": conf.get("advice"),
        "required_skills_matched": metrics.get("req_matched", 0),
        "required_skills_total": metrics.get("req_total", 0),
        "preferred_skills_matched": metrics.get("pref_matched", 0),
        "preferred_skills_total": metrics.get("pref_total", 0),
        "experience_years_candidate": metrics.get("exp_cand", 0.0),
        "experience_years_required": metrics.get("exp_req", 0.0),
        "experience_gap_years": metrics.get("exp_gap", 0.0),
        "education_gate": metrics.get("education_gate"),
        "education_requirement": metrics.get("education_req")
    }

    try:
        # Pass the dynamic dictionary
        analysis = AnalysisRepository(db).create(session_id=resume.session_id, resume_id=resume.id, job_id=job.id, analysis_data=analysis_data)

        recommendations_raw = match_result.get("recommendations", [])
        for rec in recommendations_raw:
            db.add(Recommendation(analysis_id=analysis.id, **rec))
        db.commit()
        db.refresh(analysis)

        return build_analyze_response(analysis, cached=False, debug_info=match_result.get("debug_info"))
    except Exception as e:
        logger.error(f"Failed to create analysis: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to save analysis results.")

@router.get("", response_model=list[AnalyzeResponse])
async def list_analyses(request: Request, db: Session = Depends(get_db)):
    session_id_str = request.headers.get("X-Session-ID") or request.cookies.get("session_id")
    analyses = []
    if session_id_str:
        try:
            session_id = UUID(session_id_str)
            analyses = db.query(Analysis).join(Resume, Analysis.resume_id == Resume.id).filter(Resume.session_id == session_id).order_by(Analysis.created_at.desc()).all()
        except Exception as e:
            logger.error(f"Error querying analyses for session {session_id_str}: {e}")
    
    # If no session-specific analyses found (or session_id missing/new), fall back to returning all analyses
    if not analyses:
        analyses = db.query(Analysis).order_by(Analysis.created_at.desc()).all()
        
    return [build_analyze_response(a) for a in analyses]


@router.get("/{analysis_id}", response_model=AnalyzeResponse)
async def get_analysis(analysis_id: UUID, db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis: raise HTTPException(status_code=404, detail="Analysis not found")
    return build_analyze_response(analysis)

@router.delete("/{analysis_id}", status_code=204)
async def delete_analysis(analysis_id: UUID, db: Session = Depends(get_db)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis: raise HTTPException(status_code=404, detail="Analysis not found")
    db.query(Recommendation).filter(Recommendation.analysis_id == analysis_id).delete()
    db.delete(analysis)
    db.commit()
    return None
