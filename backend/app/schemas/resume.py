from pydantic import BaseModel, UUID4
from typing import List, Optional
from datetime import datetime

# Common models used within the parsed data
class Education(BaseModel):
    degree: Optional[str] = None
    institution: Optional[str] = None
    year: Optional[str] = None

class Experience(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None  # professional|internship|freelance|academic

class Project(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    technologies: List[str] = []

class ResumeParsedData(BaseModel):
    name: Optional[str] = None
    summary: Optional[str] = None
    education: List[Education] = []
    experience: List[Experience] = []
    projects: List[Project] = []
    skills: List[str] = []
    certifications: List[str] = []

# Response Model for POST /api/resumes
class ResumeResponse(BaseModel):
    id: UUID4
    filename: str
    parsed_data: Optional[ResumeParsedData] = None
    created_at: datetime

    class Config:
        from_attributes = True
