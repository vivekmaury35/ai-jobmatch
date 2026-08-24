# Scoring version - increment when logic/weights change to invalidate cache
SCORING_VERSION = "4.0.0"  # v4: compound-requirement decomposition, priority-weighted
                            # category scoring, certifications scored separately,
                            # semantic responsibility cross-checking.

# Category weights for computing a weighted overall score from sub-scores.
# Used as a consistency check against the LLM's overall_match_percentage_justified,
# and as the actual scoring formula when the LLM's figure deviates too far.
# Sum is exactly 100. Intentionally a plain dict so weights are easy to tune
# without touching scoring logic (spec item 12).
CATEGORY_WEIGHTS = {
    "technical_skills": 28.0,     # Core technical skill + tool match (TECHNICAL + TOOL)
    "soft_skills": 14.0,          # Behavioral traits, evidence-based
    "ai_tools": 5.0,              # AI tool proficiency (when applicable)
    "responsibilities": 10.0,     # Duty/deliverable alignment
    "experience": 10.0,           # Years and relevance
    "education": 13.0,            # Degree/eligibility gate
    "project_evidence": 10.0,     # Portfolio/project alignment
    "location": 5.0,              # Location / work mode fit
    "certifications": 5.0,        # Certification match - low weight, see PRIORITY_WEIGHTS
}
# ^ Roughly mirrors the suggested defaults (Technical 30% / Responsibilities+
# Experience 20% / Soft 15% / Education 15% / Projects 10% / AI-Tools 5% /
# Location 5%), while keeping each existing sub-score its own bucket and
# adding a small, separate certifications weight per spec item 8.

# Maximum allowed deviation between LLM overall and computed weighted average.
# If deviation exceeds this, the computed average is used instead.
OVERALL_SCORE_MAX_DEVIATION = 12.0

# How much a single requirement's match/miss contributes to its category's
# score, based on the requirement's priority (spec item 13). Mandatory gaps
# hurt; preferred/optional/informational gaps barely move the needle.
PRIORITY_WEIGHTS = {
    "MANDATORY": 1.0,
    "IMPORTANT": 0.8,
    "PREFERRED": 0.4,
    "OPTIONAL": 0.2,
    "INFORMATIONAL": 0.0,
}

# Minimum cosine similarity (all-MiniLM-L6-v2 embeddings) for a resume
# sentence to be treated as semantic evidence for a RESPONSIBILITY/SOFT
# requirement the LLM marked as missing (spec item 7).
SEMANTIC_MATCH_THRESHOLD = 0.55
