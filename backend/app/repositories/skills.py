from typing import List, Optional, Dict, Tuple
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.skill import Skill
from app.models.resume import ResumeSkill
from app.models.job import JobSkill
from app.repositories.base import BaseRepository

class SkillRepository(BaseRepository):
    def get_all(self) -> List[Skill]:
        return self.db.query(Skill).all()

    def get_by_canonical_name(self, name: str) -> Optional[Skill]:
        return self.db.query(Skill).filter(Skill.canonical_name == name.lower()).first()

    def create_resume_skill(self, resume_id: UUID, raw_text: str, evidence_source: str,
                            confidence: float, skill_id: Optional[UUID] = None) -> ResumeSkill:
        rs = ResumeSkill(
            resume_id=resume_id,
            skill_id=skill_id,
            raw_text=raw_text,
            evidence_source=evidence_source,
            confidence=confidence
        )
        self.db.add(rs)
        return rs

    def create_job_skill(self, job_id: UUID, raw_text: str, required: bool = False,
                         importance: float = 1.0, skill_id: Optional[UUID] = None) -> JobSkill:
        js = JobSkill(
            job_id=job_id,
            skill_id=skill_id,
            raw_text=raw_text,
            required=required,
            importance=importance
        )
        self.db.add(js)
        return js
