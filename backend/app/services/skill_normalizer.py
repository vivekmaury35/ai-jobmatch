import re
from typing import Dict, List, Optional, Tuple
from rapidfuzz import process, fuzz
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.skill import Skill
from app.repositories.skills import SkillRepository

class SkillNormalizerService:
    def __init__(self, db: Session):
        self.db = db
        self.skill_repo = SkillRepository(db)

        # Pre-load taxonomy into memory for fast matching
        # Data struct: { "lowercase_exact_or_alias_string": Skill_Object }
        self.taxonomy: Dict[str, Skill] = {}
        # List of all searchable strings for RapidFuzz
        self.searchable_strings: List[str] = []

        self._load_taxonomy()

    def _load_taxonomy(self):
        """Loads canonical names and aliases into memory dictionaries"""
        all_skills = self.skill_repo.get_all()
        for skill in all_skills:
            # Add Canonical name
            canonical_lower = skill.canonical_name.lower().strip()
            self.taxonomy[canonical_lower] = skill
            self.searchable_strings.append(canonical_lower)

            # Add Aliases
            if skill.aliases:
                for alias in skill.aliases:
                    alias_lower = alias.lower().strip()
                    # Prevent alias overwriting a canonical name if there's a conflict
                    if alias_lower not in self.taxonomy:
                        self.taxonomy[alias_lower] = skill
                        self.searchable_strings.append(alias_lower)

        # Ensure fast uniqueness
        self.searchable_strings = list(set(self.searchable_strings))

    def _clean_string(self, text: str) -> str:
        """Standardize casing and basic punctuation"""
        return re.sub(r'[^a-zA-Z0-9#\+\-\.\s]', '', text.lower().strip())

    def normalize(self, raw_skill: str) -> Tuple[Optional[Skill], str]:
        """
        Takes a raw skill string and attempts to resolve it against the taxonomy.
        Returns (Skill Model, Match Type String) or (None, "free-text")

        Layers:
        1. Exact match (fastest)
        2. Alias match (via the loaded taxonomy dict)
        3. Fuzzy match (RapidFuzz, scoring 85+)
        4. Fallback (None)
        """
        cleaned_raw = self._clean_string(raw_skill)
        if not cleaned_raw:
            return None, "free-text"

        # 1 & 2: Exact & Alias Matching
        if cleaned_raw in self.taxonomy:
            skill = self.taxonomy[cleaned_raw]
            match_type = "exact" if cleaned_raw == skill.canonical_name else "alias"
            return skill, match_type

        # 3: Fuzzy Matching (handles typos like "Postgre SQL" -> "postgresql")
        # ExtractOne returns (Matched_String, Score_0_to_100, Index)
        best_match = process.extractOne(
            cleaned_raw,
            self.searchable_strings,
            scorer=fuzz.WRatio
        )

        if best_match:
            match_string, score, _ = best_match
            if score >= 85.0:  # 85 is usually a strict enough threshold for tech skills
                fuzzy_skill = self.taxonomy[match_string]
                return fuzzy_skill, "fuzzy"

        # 4: Fallback
        return None, "free-text"

    def populate_resume_skills(self, resume_id: UUID, raw_skills: List[str]):
        """Normalizes and saves skills found in a resume to DB"""
        for raw in set(raw_skills):  # Deduplicate natively
            skill, _ = self.normalize(raw)
            self.skill_repo.create_resume_skill(
                resume_id=resume_id,
                raw_text=raw,
                evidence_source="extracted_list", # From the LLM extraction
                confidence=1.0,
                skill_id=skill.id if skill else None
            )
        self.db.commit()

    def populate_job_skills(self, job_id: UUID, required: List[str], preferred: List[str]):
        """Normalizes and saves skills found in a JD to DB"""
        for raw in set(required):
            skill, _ = self.normalize(raw)
            self.skill_repo.create_job_skill(
                job_id=job_id,
                raw_text=raw,
                required=True,
                skill_id=skill.id if skill else None
            )

        for raw in set(preferred):
            # Careful not to duplicate if it was already in required
            if raw in required:
                continue

            skill, _ = self.normalize(raw)
            self.skill_repo.create_job_skill(
                job_id=job_id,
                raw_text=raw,
                required=False,
                skill_id=skill.id if skill else None
            )
        self.db.commit()
