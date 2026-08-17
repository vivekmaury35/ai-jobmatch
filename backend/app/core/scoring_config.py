# Scoring weights defined centrally so they are easy to explain/tune.
# Sum is exactly 100.
SCORING_WEIGHTS = {
    "skill_match": 35.0,
    "semantic_similarity": 25.0,
    "experience_match": 20.0,
    "project_evidence": 10.0,
    "education_match": 10.0
}

# Tiers of skill matching accuracy
SKILL_TIER_SCORES = {
    "exact": 1.0,
    "alias": 0.95,
    "fuzzy": 0.85,
    "related": 0.50, # matched via sentence-transformer semantics
    "missing": 0.0
}

SEMANTIC_SIMILARITY_THRESHOLD = 0.75
