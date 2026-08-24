from typing import Any, Dict, List, Optional, Literal, Union
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel

class RecommendationSchema(BaseModel):
    type: str  # add_skill, add_experience, emphasize_education, reframe_skill
    content: str
    priority: int

class AnalyzeRequest(BaseModel):
    resume_id: UUID
    job_id: UUID

class SkillEvidenceSchema(BaseModel):
    skill_name: str
    category: Literal[
        'TECHNICAL', 'TOOL', 'SOFT', 'ROLE', 'LOCATION', 'WORK_ARRANGEMENT',
        'ELIGIBILITY', 'EDUCATION_REQUIREMENT', 'AI_TOOL', 'RESPONSIBILITY',
        'LANGUAGE', 'LANGUAGE_PROFICIENCY', 'EMPLOYMENT_TYPE',
        'CERTIFICATION',  # defensive fallback only - the LLM is instructed to
                          # never use this; matching.py reroutes it into the
                          # separate `certifications` bucket if it slips through.
        'INFORMATIONAL'
    ]
    # Priority controls how heavily a miss on this requirement penalizes the
    # overall score (see PRIORITY_WEIGHTS in app/core/scoring_config.py).
    priority: Literal['MANDATORY', 'IMPORTANT', 'PREFERRED', 'OPTIONAL', 'INFORMATIONAL'] = 'IMPORTANT'
    is_required: bool
    status: Literal['SATISFIED', 'PARTIALLY_SATISFIED', 'MISSING_BUT_OPTIONAL', 'MISSING_AND_REQUIRED']
    matched_as: Optional[str] = None
    reasoning: str
    evidence_snippet: Optional[str] = None
    source_section: Optional[str] = None
    proficiency_level: Optional[str] = None

    # Compound-requirement decomposition, e.g. "Microsoft Office Suite (Word,
    # Excel, PowerPoint)" -> atomic_components=["Word","Excel","PowerPoint"],
    # logical_operator="AND". Populated by the LLM when it recognizes a
    # compound phrase; independently re-verified/derived deterministically in
    # app/services/matching.py via app/services/skill_normalization.py.
    atomic_components: Optional[List[str]] = None
    logical_operator: Optional[Literal['AND', 'OR']] = None

    # Explainability (spec item 15): the literal resume evidence that
    # justified a match (quoted sentence, or matched atom names).
    matched_resume_evidence: Optional[List[str]] = None

    # Deterministic re-verification results, filled in by matching.py (not
    # by the LLM). Optional so LLM output validates without them.
    match_status: Optional[Literal['FULL_MATCH', 'PARTIAL_MATCH', 'WEAK_MATCH', 'NO_MATCH']] = None
    match_score: Optional[float] = None

class CertificationEvidenceSchema(BaseModel):
    """Certifications are tracked and scored completely separately from
    technical skills (spec item 8) so a long list of nice-to-have
    certifications never masquerades as mandatory technical requirements."""
    name: str
    priority: Literal['REQUIRED', 'PREFERRED', 'RECOMMENDED', 'INFORMATIONAL'] = 'PREFERRED'
    matched: bool = False
    matched_resume_evidence: Optional[str] = None
    reasoning: str = ""

class ExpertEvaluationSchema(BaseModel):
    """ The 100% LLM Brain Output Structure explicitly defining soft skills vs technical rules """
    overall_match_percentage_justified: float

    # Core Requirements Breakdowns
    all_requirements_evaluation: List[SkillEvidenceSchema]

    # Certifications are extracted and evaluated separately from technical
    # skills/tools (spec item 8) - never blended into all_requirements_evaluation.
    certifications: List[CertificationEvidenceSchema] = []

    # Required Tech Skills array isolation
    required_technical_skills_met: int
    required_technical_skills_total_logical: int

    # Sub-Score Breakdown — None means "LLM did not populate"; 0.0 means "genuinely zero"
    technical_skills_score: Optional[float] = None
    soft_skills_score: Optional[float] = None
    ai_tools_score: Optional[float] = None
    responsibilities_score: Optional[float] = None
    education_score: Optional[float] = None
    experience_score: Optional[float] = None
    project_evidence_score: Optional[float] = None
    location_score: Optional[float] = None
    certification_score: Optional[float] = None

    # Experience grouping
    years_required_by_job: float
    years_found_on_resume: float
    experience_status: Literal['MET', 'GAP', 'EXCEEDS', 'FRESHER_ELIGIBLE']

    # Education grouping
    education_gate: Literal['MET', 'PREFERRED_MISSING', 'REQUIRED_MISSING', 'NOT_APPLICABLE']
    detected_education: str

    # Prescriptive Coach Output
    analysis_explanation: str
    actionable_recommendations: List[RecommendationSchema]

class AnalyzeResponse(BaseModel):
    id: UUID
    resume_id: UUID
    job_id: UUID
    job_title: Optional[str] = None

    # Confidence tier
    confidence_tier: Optional[str] = None
    tier_label: Optional[str] = None
    tier_advice: Optional[str] = None

    # Scores
    overall_score: float
    required_skills_matched: int = 0
    required_skills_total: int = 0
    preferred_skills_matched: int = 0
    preferred_skills_total: int = 0
    experience_years_candidate: float = 0.0
    experience_years_required: float = 0.0
    experience_gap_years: float = 0.0

    education_gate: Optional[str] = None
    education_requirement: Optional[str] = None

    # Sub-Scores
    skill_score: float = 0.0
    experience_score: float = 0.0
    education_score: float = 0.0
    project_evidence_score: float = 0.0
    soft_skills_score: float = 0.0
    ai_tools_score: float = 0.0
    responsibilities_score: float = 0.0
    location_score: float = 0.0
    certification_score: float = 100.0

    # Skills Arrays for the UI Layout
    matched_skills: List[Dict[str, Any]]
    missing_skills: List[Dict[str, Any]]
    related_skills: List[Dict[str, Any]]

    # Certifications, scored and displayed separately from technical skills (item 8)
    certifications: List[Dict[str, Any]] = []

    explanation: Optional[str] = None
    recommendations: List[RecommendationSchema] = []

    cached: bool = False
    created_at: Optional[datetime] = None

    # Populated only when the analyze request is made with ?debug=true.
    # Never persisted to the database. See spec item 17.
    debug_info: Optional[Dict[str, Any]] = None



