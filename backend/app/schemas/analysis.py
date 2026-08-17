from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    resume_id: UUID
    job_id: UUID


class AnalyzeResponse(BaseModel):
    id: UUID
    resume_id: UUID
    job_id: UUID

    overall_score: float

    skill_score: float
    semantic_score: float
    experience_score: float
    education_score: float
    project_evidence_score: float

    matched_skills: List[Dict[str, Any]]
    missing_skills: List[Dict[str, Any]]
    related_skills: List[Dict[str, Any]]

    explanation: Optional[str] = None
    cached: bool = False
