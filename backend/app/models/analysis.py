from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base

class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), index=True, nullable=False)
    resume_id = Column(UUID(as_uuid=True), ForeignKey("resumes.id"), nullable=False)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)

    scoring_version = Column(String(50), nullable=True) # E.g., 'v2.0.0' for cache invalidation

    confidence_tier = Column(String(50), nullable=True)
    tier_label = Column(String(100), nullable=True)
    tier_advice = Column(String, nullable=True)

    required_skills_matched = Column(Integer, default=0)
    required_skills_total = Column(Integer, default=0)
    preferred_skills_matched = Column(Integer, default=0)
    preferred_skills_total = Column(Integer, default=0)

    experience_years_candidate = Column(Float, default=0.0)
    experience_years_required = Column(Float, default=0.0)
    experience_gap_years = Column(Float, default=0.0)

    education_gate = Column(String(50), nullable=True)
    education_requirement = Column(String, nullable=True)

    overall_score = Column(Float, nullable=True)
    skill_score = Column(Float, nullable=True)
    experience_score = Column(Float, nullable=True)
    education_score = Column(Float, nullable=True)
    project_evidence_score = Column(Float, nullable=True)
    soft_skills_score = Column(Float, nullable=True)
    ai_tools_score = Column(Float, nullable=True)
    responsibilities_score = Column(Float, nullable=True)
    location_score = Column(Float, nullable=True)
    certification_score = Column(Float, nullable=True)

    matched_skills = Column(JSONB, nullable=True)
    missing_skills = Column(JSONB, nullable=True)
    related_skills = Column(JSONB, nullable=True) # Adding this so it can be correctly retrieved from cache
    explanation = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    resume = relationship("Resume", back_populates="analyses")
    job = relationship("Job", back_populates="analyses")
    recommendations = relationship("Recommendation", back_populates="analysis")

class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    analysis_id = Column(UUID(as_uuid=True), ForeignKey("analyses.id"), nullable=False)
    type = Column(String, nullable=False)
    content = Column(String, nullable=False)
    priority = Column(Integer, default=1)

    analysis = relationship("Analysis", back_populates="recommendations")
