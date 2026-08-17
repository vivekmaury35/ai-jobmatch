from sqlalchemy import Column, String, DateTime, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base

class Resume(Base):
    __tablename__ = "resumes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), index=True, nullable=False)
    filename = Column(String, nullable=False)
    raw_text = Column(String, nullable=False)
    parsed_data = Column(JSONB, nullable=True)
    content_hash = Column(String, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    skills = relationship("ResumeSkill", back_populates="resume")
    analyses = relationship("Analysis", back_populates="resume")

class ResumeSkill(Base):
    __tablename__ = "resume_skills"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    skill_id = Column(UUID(as_uuid=True), ForeignKey("skills.id"), nullable=True)
    raw_text = Column(String, nullable=False)
    evidence_source = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)

    resume = relationship("Resume", back_populates="skills")
    skill = relationship("Skill")
