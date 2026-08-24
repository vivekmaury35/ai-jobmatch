from fastapi import APIRouter, HTTPException, Depends, Request, Response
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.repositories.base import SessionRepository, JobRepository
from app.schemas.job import JobCreateRequest, JobResponse, JobParsedData
from app.services.ai import AIService, AIExtractionError
from app.services.skill_normalizer import SkillNormalizerService
import hashlib

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("", response_model=JobResponse, status_code=201)
async def analyze_job(request: Request, response: Response, job_input: JobCreateRequest, db: Session = Depends(get_db)):
    """
    FR-8, FR-9, FR-10: Accepts JD text, validates length, extracts structured data via LLM.
    """
    raw_text = job_input.raw_text.strip()
    word_count = len(raw_text.split())

    # FR-9: Reject if too short
    if word_count < 50:
         raise HTTPException(status_code=400, detail={
            "code": "JD_TOO_SHORT",
            "message": "Please paste the full job description (at least 50 words) for an accurate analysis."
        })

    # AI Service Execution
    ai_service = AIService()
    try:
        # Provide the Pydantic class map directly to the service
        parsed_job_data: JobParsedData = await ai_service.extract_structured(
            text=raw_text,
            schema=JobParsedData,
            extraction_type="Job Description"
        )
    except AIExtractionError as e:
         raise HTTPException(status_code=502, detail={
            "code": "EXTRACTION_FAILED",
            "message": str(e)
        })

    # Prepare for persistence
    content_hash = hashlib.sha256(raw_text.encode('utf-8')).hexdigest()

    session_id_str = request.headers.get("X-Session-ID") or request.cookies.get("session_id")
    session_id = UUID(session_id_str) if session_id_str else None

    session_repo = SessionRepository(db)
    current_session = session_repo.get_or_create(session_id)

    # Keep the frontend's session in sync, same as the resume upload endpoint.
    response.headers["X-Session-ID"] = str(current_session.id)
    response.set_cookie(key="session_id", value=str(current_session.id), httponly=True, samesite="lax", max_age=30*24*60*60)

    job_repo = JobRepository(db)
    job = job_repo.create(
        session_id=current_session.id,
        title=parsed_job_data.title,
        raw_text=raw_text,
        content_hash=content_hash,
        parsed_data=parsed_job_data.model_dump()
    )

    # FR-12: Normalize and populate job_skills
    normalizer = SkillNormalizerService(db)
    normalizer.populate_job_skills(
        job_id=job.id,
        required=parsed_job_data.required_skills,
        preferred=parsed_job_data.preferred_skills
    )

    return job
