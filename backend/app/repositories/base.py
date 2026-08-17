from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.models.session import SessionModel
from app.models.resume import Resume
from app.models.job import Job
from app.models.analysis import Analysis

class BaseRepository:
    def __init__(self, db: Session):
        self.db = db

class SessionRepository(BaseRepository):
    def get_or_create(self, session_id: Optional[UUID] = None) -> SessionModel:
        if session_id:
            db_session = self.db.query(SessionModel).filter(SessionModel.id == session_id).first()
            if db_session:
                return db_session

        new_session = SessionModel()
        self.db.add(new_session)
        self.db.commit()
        self.db.refresh(new_session)
        return new_session

class ResumeRepository(BaseRepository):
    def get_by_id(self, resume_id: UUID) -> Optional[Resume]:
        return self.db.query(Resume).filter(Resume.id == resume_id).first()

    def get_by_content_hash(self, session_id: UUID, content_hash: str) -> Optional[Resume]:
        return self.db.query(Resume).filter(
            Resume.session_id == session_id,
            Resume.content_hash == content_hash
        ).first()

    def create(self, session_id: UUID, filename: str, raw_text: str, content_hash: str, parsed_data: dict = None) -> Resume:
        resume = Resume(
            session_id=session_id,
            filename=filename,
            raw_text=raw_text,
            content_hash=content_hash,
            parsed_data=parsed_data
        )
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume

class JobRepository(BaseRepository):
    def get_by_id(self, job_id: UUID) -> Optional[Job]:
        return self.db.query(Job).filter(Job.id == job_id).first()

    def get_by_content_hash(self, session_id: UUID, content_hash: str) -> Optional[Job]:
        return self.db.query(Job).filter(
            Job.session_id == session_id,
            Job.content_hash == content_hash
        ).first()

    def create(self, session_id: UUID, title: str, raw_text: str, content_hash: str, parsed_data: dict = None) -> Job:
        job = Job(
            session_id=session_id,
            title=title,
            raw_text=raw_text,
            content_hash=content_hash,
            parsed_data=parsed_data
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

class AnalysisRepository(BaseRepository):
    def get_by_id(self, analysis_id: UUID) -> Optional[Analysis]:
        return self.db.query(Analysis).filter(Analysis.id == analysis_id).first()

    def get_by_resume_and_job(self, resume_id: UUID, job_id: UUID) -> Optional[Analysis]:
        return self.db.query(Analysis).filter(
            Analysis.resume_id == resume_id,
            Analysis.job_id == job_id
        ).first()

    def create(self, session_id: UUID, resume_id: UUID, job_id: UUID, analysis_data: dict) -> Analysis:
        analysis = Analysis(
            session_id=session_id,
            resume_id=resume_id,
            job_id=job_id,
            **analysis_data
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis
