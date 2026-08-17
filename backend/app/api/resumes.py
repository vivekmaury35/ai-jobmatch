from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.repositories.base import SessionRepository, ResumeRepository
from app.services.resume_parser import ResumeParserService, ScannedPDFError
from app.services.ai import AIService, AIExtractionError
from app.schemas.resume import ResumeResponse, ResumeParsedData

router = APIRouter(prefix="/resumes", tags=["resumes"])

@router.post("", response_model=ResumeResponse, status_code=201)
async def upload_resume(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    FR-1, FR-2, FR-4: Uploads a PDF resume, parses its text, and saves it.
    """

    # 1. Validate file type and size
    file_bytes = await file.read()

    if len(file_bytes) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "FILE_TOO_LARGE",
                "message": "Resume file cannot exceed 5MB.",
            },
        )

    filename = (file.filename or "").lower()

    if not filename.endswith(".pdf") or not file_bytes.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail={
                "code": "INVALID_FILE_TYPE",
                "message": "Only PDF files are supported.",
            },
        )

    # 2. Extract document text via pure Python heuristics
    parser_service = ResumeParserService()

    try:
        raw_text = parser_service.extract_text_from_pdf(file_bytes)

    except ScannedPDFError as e:
        raise HTTPException(
            status_code=422,
            detail={
                "code": "SCANNED_PDF_UNSUPPORTED",
                "message": str(e),
            },
        )

    except Exception:
        raise HTTPException(
            status_code=502,
            detail={
                "code": "EXTRACTION_FAILED",
                "message": "Failed to parse the PDF file.",
            },
        )

    sectioned_text = parser_service.heuristically_chunk_sections(raw_text)

    # 3. AI Service structured extraction via Gemini API
    ai_service = AIService()
    try:
        # We pass the heuristically chunked text as a string to the AI model
        text_for_ai = "\n\n".join([f"---{k.upper()}---\n{v}" for k, v in sectioned_text.items()])

        parsed_resume_data: ResumeParsedData = await ai_service.extract_structured(
            text=text_for_ai,
            schema=ResumeParsedData,
            extraction_type="Resume"
        )
    except AIExtractionError as e:
         raise HTTPException(status_code=502, detail={
            "code": "EXTRACTION_FAILED",
            "message": str(e)
        })

    # 4. Persistence
    content_hash = parser_service.get_content_hash(raw_text)

    # Automatically derive or create a session
    session_id_str = request.cookies.get("session_id")
    session_id = UUID(session_id_str) if session_id_str else None

    session_repo = SessionRepository(db)
    current_session = session_repo.get_or_create(session_id)

    resume_repo = ResumeRepository(db)

    # Update logic to save the fully structured Pydantic dump
    resume = resume_repo.create(
        session_id=current_session.id,
        filename=file.filename,
        raw_text=raw_text,
        content_hash=content_hash,
        parsed_data=parsed_resume_data.model_dump(),
    )

    return resume
