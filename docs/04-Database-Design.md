# AI JobMatch — Database Design

## 1. Overview
PostgreSQL, accessed via SQLAlchemy 2.x with Alembic migrations. No multi-tenant auth for MVP — rows are scoped by a `session_id` (opaque string stored in an httpOnly cookie), not a real `user_id`/login. This can be upgraded to real auth later without a schema rewrite (just add a `users` table and backfill `session_id → user_id`).

## 2. Entity List
- sessions
- resumes
- jobs
- skills (taxonomy)
- resume_skills
- job_skills
- analyses
- recommendations

## 3. Table Definitions

### 3.1 `sessions`
| Column | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| created_at | timestamptz | default now() |
| last_seen_at | timestamptz | updated on each request |

### 3.2 `resumes`
| Column | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| session_id | UUID, FK → sessions.id | |
| filename | text | original upload filename |
| raw_text | text | extracted PDF text |
| parsed_data | jsonb | structured `ResumeProfile` (name, summary, education[], experience[], projects[], skills[], certifications[]) |
| content_hash | text | sha256 of raw_text, for cache/dedup |
| created_at | timestamptz | default now() |

Index: `content_hash` (for cache lookups), `session_id`.

### 3.3 `jobs`
| Column | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| session_id | UUID, FK → sessions.id | |
| title | text | extracted job title |
| raw_text | text | pasted JD text |
| parsed_data | jsonb | structured `JobProfile` (required_skills[], preferred_skills[], responsibilities[], experience_years_required, education_requirement) |
| content_hash | text | sha256 of raw_text |
| created_at | timestamptz | default now() |

Index: `content_hash`, `session_id`.

### 3.4 `skills` (taxonomy)
| Column | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| canonical_name | text, unique | e.g. `"postgresql"` |
| display_name | text | e.g. `"PostgreSQL"` |
| aliases | text[] | e.g. `{"postgres", "pgsql", "postgre sql"}` |
| category | text | e.g. `"database"`, `"language"`, `"framework"`, `"cloud"` |

Seed with ≥100 common tech skills at migration time (seed script, not hardcoded in app code).

### 3.5 `resume_skills`
| Column | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| resume_id | UUID, FK → resumes.id | |
| skill_id | UUID, FK → skills.id, nullable | null if skill wasn't in taxonomy (free-text) |
| raw_text | text | the exact string as it appeared |
| evidence_source | text | `"skills_section"` \| `"experience"` \| `"project"` \| `"certification"` |
| confidence | float | 0–1, from extraction |

### 3.6 `job_skills`
| Column | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| job_id | UUID, FK → jobs.id | |
| skill_id | UUID, FK → skills.id, nullable | |
| raw_text | text | |
| required | boolean | required vs preferred |
| importance | float | optional weighting, default 1.0 |

### 3.7 `analyses`
| Column | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| session_id | UUID, FK → sessions.id | |
| resume_id | UUID, FK → resumes.id | |
| job_id | UUID, FK → jobs.id | |
| overall_score | float | 0–100 |
| skill_score | float | 0–100 |
| semantic_score | float | 0–100 |
| experience_score | float | 0–100 |
| education_score | float | 0–100 |
| project_evidence_score | float | 0–100 |
| matched_skills | jsonb | list of {skill, tier, evidence} |
| missing_skills | jsonb | list of {skill} |
| explanation | text | LLM-generated, grounded in scores above |
| created_at | timestamptz | default now() |

Index: `(resume_id, job_id)` unique-ish for cache lookups (same resume+JD → reuse), `session_id`.

### 3.8 `recommendations`
| Column | Type | Notes |
|---|---|---|
| id | UUID, PK | |
| analysis_id | UUID, FK → analyses.id | |
| type | text | e.g. `"add_skill"`, `"rephrase_bullet"`, `"quantify_impact"` |
| content | text | the suggestion text |
| priority | int | 1 = highest |

## 4. Relationships Summary
```
sessions 1───* resumes
sessions 1───* jobs
sessions 1───* analyses
resumes  1───* resume_skills ───* skills
jobs     1───* job_skills   ───* skills
resumes  1───* analyses *───1 jobs
analyses 1───* recommendations
```

## 5. Caching Strategy
Before running a full analysis, check for an existing `analyses` row with matching `resume_id` + `job_id` (both derived by `content_hash` lookups on `resumes`/`jobs`). If found, return the cached result instead of re-calling AI providers. This is the caching feature called out as valuable in the original research — implement it via `content_hash`, not a separate cache table, to keep MVP schema simple.

## 6. Migration Notes for Claude Code
- Use Alembic from the start (`alembic init migrations`), even for the first table — retrofitting migrations later is painful.
- Write a seed script (`backend/scripts/seed_skills.py`) to populate the `skills` taxonomy; do not hardcode taxonomy in Python constants.
- Use `jsonb` (not `json`) for all structured columns for indexing/query flexibility.
