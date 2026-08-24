from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request, Response
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.repositories.base import SessionRepository, ResumeRepository
from app.services.resume_parser import ResumeParserService, ScannedPDFError
from app.services.ai import AIService, AIExtractionError
from app.services.skill_normalizer import SkillNormalizerService
from app.schemas.resume import ResumeResponse, ResumeParsedData

router = APIRouter(prefix="/resumes", tags=["resumes"])

@router.post("", response_model=ResumeResponse, status_code=201)
async def upload_resume(
    request: Request,
    response: Response,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    FR-1, FR-2, FR-4: Uploads a PDF resume, extracts raw text, and delegates full structuring directly to AI.
    """
    file_bytes = await file.read()

    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail={"code": "FILE_TOO_LARGE", "message": "Resume file cannot exceed 5MB."}
        )

    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf") or not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail={"code": "INVALID_FILE_TYPE", "message": "Only PDF files are supported."}
        )

    # 1. Extract raw text from PDF
    parser_service = ResumeParserService()
    try:
        raw_text = parser_service.extract_text_from_pdf(file_bytes)
    except ScannedPDFError as e:
        raise HTTPException(status_code=422, detail={"code": "SCANNED_PDF_UNSUPPORTED", "message": str(e)})
    except Exception:
        raise HTTPException(status_code=502, detail={"code": "EXTRACTION_FAILED", "message": "Failed to parse the PDF file."})

    # 2. Direct AI Service structured extraction
    # We bypass heuristic chunking and let the AI brain read the whole raw document
    ai_service = AIService()
    try:
        parsed_resume_data: ResumeParsedData = await ai_service.extract_structured(
            text=raw_text, # Just feed raw text directly
            schema=ResumeParsedData,
            extraction_type="Resume"
        )
    except AIExtractionError as e:
         raise HTTPException(status_code=502, detail={"code": "EXTRACTION_FAILED", "message": str(e)})

    # 3. Persistence
    content_hash = parser_service.get_content_hash(raw_text)

    # Trust X-Session-ID header first (fixes localhost CORS dropping cookies)
    session_id_str = request.headers.get("X-Session-ID") or request.cookies.get("session_id")
    session_id = UUID(session_id_str) if session_id_str else None

    session_repo = SessionRepository(db)
    current_session = session_repo.get_or_create(session_id)
    resume_repo = ResumeRepository(db)

    resume = resume_repo.create(
        session_id=current_session.id,
        filename=file.filename,
        raw_text=raw_text,
        content_hash=content_hash,
        parsed_data=parsed_resume_data.model_dump(),
    )

    normalizer = SkillNormalizerService(db)
    normalizer.populate_resume_skills(resume_id=resume.id, raw_skills=parsed_resume_data.skills)

    # Return session ID via custom response header so frontend can store it
    response.headers["X-Session-ID"] = str(current_session.id)
    response.set_cookie(key="session_id", value=str(current_session.id), httponly=True, samesite="lax", max_age=30*24*60*60)

    return resume
