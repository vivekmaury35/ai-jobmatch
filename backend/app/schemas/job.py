from pydantic import BaseModel, UUID4
from typing import List, Optional
from datetime import datetime

class JobParsedData(BaseModel):
    title: Optional[str] = None
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    responsibilities: List[str] = []
    experience_years_required: Optional[int] = None
    education_requirement: Optional[str] = None

class JobCreateRequest(BaseModel):
    raw_text: str

class JobResponse(BaseModel):
    id: UUID4
    title: Optional[str] = None
    parsed_data: Optional[JobParsedData] = None
    created_at: datetime

    class Config:
        from_attributes = True
