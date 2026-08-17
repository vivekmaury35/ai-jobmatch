from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Float
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base

class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), index=True, nullable=False)
    title = Column(String, nullable=True)
    raw_text = Column(String, nullable=False)
    parsed_data = Column(JSONB, nullable=True)
    content_hash = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    skills = relationship("JobSkill", back_populates="job")
    analyses = relationship("Analysis", back_populates="job")

class JobSkill(Base):
    __tablename__ = "job_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=True)
    raw_text = Column(String, nullable=False)
    required = Column(Boolean, default=False)
    importance = Column(Float, default=1.0)

    job = relationship("Job", back_populates="skills")
    skill = relationship("Skill")
