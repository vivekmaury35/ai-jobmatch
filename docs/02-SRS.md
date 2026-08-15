# AI JobMatch — Software Requirements Specification (SRS)

## 1. Purpose
This document translates the PRD into concrete, testable functional and non-functional requirements for implementation by Claude Code.

## 2. Functional Requirements

### 2.1 Resume Ingestion
- **FR-1**: System shall accept a single PDF file upload, max 5 MB.
- **FR-2**: System shall reject non-PDF files with a clear error message.
- **FR-3**: System shall extract raw text from the PDF using PyMuPDF.
- **FR-4**: If extracted text length is below a defined threshold (e.g., <100 characters), system shall treat the PDF as likely scanned/image-based and return an error: "This resume appears to be a scanned image. Please upload a text-based PDF." (OCR is explicitly out of scope for MVP.)
- **FR-5**: System shall detect resume sections (Contact, Summary, Education, Experience, Projects, Skills, Certifications) from raw text using heading heuristics before sending to the LLM.
- **FR-6**: System shall send section-chunked text to the LLM with a schema-constrained prompt to produce a structured `ResumeProfile` JSON object, validated against a Pydantic schema.
- **FR-7**: If LLM output fails schema validation, system shall retry once with an error-correction prompt; if it fails again, return a user-facing error.

### 2.2 Job Description Ingestion
- **FR-8**: System shall accept pasted plain-text job description, minimum 50 words, maximum ~10,000 characters.
- **FR-9**: Below minimum length, system shall reject with: "Please paste the full job description (at least 50 words) for an accurate analysis."
- **FR-10**: System shall extract a structured `JobProfile` (title, required_skills[], preferred_skills[], responsibilities[], experience_years_required, education_requirement) via schema-constrained LLM call, validated against Pydantic.

### 2.3 Skill Normalization
- **FR-11**: System shall maintain a skill taxonomy (canonical name + aliases), stored in the database, seeded with at least 100 common tech skills at launch.
- **FR-12**: System shall normalize all extracted skills (resume and JD) against this taxonomy before matching.
- **FR-13**: Skills with no taxonomy match shall be kept as free-text and matched only via semantic similarity, not exact/alias matching.

### 2.4 Matching Engine
- **FR-14**: System shall classify each required/preferred JD skill against the candidate's normalized skills as one of: `exact`, `alias`, `related` (semantic similarity above threshold, e.g. >0.75 cosine), or `missing`.
- **FR-15**: System shall compute sub-scores: skill_score, semantic_score, experience_score, education_score, project_evidence_score — each 0–100.
- **FR-16**: System shall compute overall_score as a fixed weighted sum of sub-scores (weights defined in Architecture doc §5) — this computation shall be deterministic Python code, not an LLM call.
- **FR-17**: Given identical resume text and JD text, the system shall produce the identical overall_score on repeated runs (allow LLM-extraction step to be cached/pinned so re-runs use identical structured input to the deterministic scorer).
- **FR-18**: System shall compute experience_years from parsed experience entries and compare against JD's required years, producing an experience_gap value.

### 2.5 Explanation & Recommendations
- **FR-19**: System shall generate a natural-language explanation via LLM, given ONLY the computed scores, matched/missing skill lists, and extracted evidence as context — the prompt shall explicitly instruct the LLM not to alter or invent the score.
- **FR-20**: System shall generate 2–4 resume improvement suggestions, each grounded in specific extracted resume content (no invented achievements) — prompt shall explicitly forbid fabrication.

### 2.6 Persistence & History
- **FR-21**: System shall persist each analysis (resume snapshot, JD snapshot, all scores, explanation, recommendations, timestamp) associated with a session/device identifier.
- **FR-22**: System shall provide a list endpoint returning past analyses for the current session, ordered by recency.
- **FR-23**: System shall provide a detail endpoint returning the full result for a single past analysis by ID.

### 2.7 Error Handling (applies system-wide)
- **FR-24**: All external AI calls shall have a timeout (recommend 30s) and shall surface a user-facing error on timeout/failure rather than hanging.
- **FR-25**: All AI calls shall have at least one automatic retry on transient failure (5xx, timeout) before surfacing an error.
- **FR-26**: Any unhandled backend exception shall return a structured JSON error (not a raw stack trace) with an HTTP 4xx/5xx status.

## 3. Non-Functional Requirements

- **NFR-1 (Performance)**: End-to-end analysis (upload → result) shall complete in under 15 seconds for a typical 1–2 page resume and JD, under normal network conditions.
- **NFR-2 (Reliability)**: Independent extraction steps (resume parsing, JD parsing) shall run concurrently (async), not sequentially, where they don't depend on each other.
- **NFR-3 (Cost)**: System shall use local Sentence Transformers for embeddings (no per-call embedding API cost) and shall keep LLM calls to a minimum: one call for resume extraction, one for JD extraction, one for explanation/recommendations (3 total per analysis, not per-skill).
- **NFR-4 (Security)**: No AI provider API key shall ever be present in frontend code or any `NEXT_PUBLIC_*` environment variable. All AI calls originate server-side from FastAPI.
- **NFR-5 (Portability)**: The system shall run fully via `docker-compose up` for local development (Postgres at minimum containerized; frontend/backend may run natively or containerized).
- **NFR-6 (Explainability)**: No score-bearing output may be produced solely by an uncontrolled LLM call — every score must trace to deterministic code the builder can point to and explain.
- **NFR-7 (Reproducibility)**: The deterministic scoring function shall be pure (same structured input → same output), independent of LLM sampling.
- **NFR-8 (Data honesty)**: The system shall never label output "ATS score" or "ATS certified" — only "ATS-style keyword analysis," to avoid an inaccurate/misleading claim.

## 4. Assumptions
- Single environment (dev/demo), no need for staging/prod parity infrastructure.
- Traffic volume is low (personal + recruiter demo use) — no load-balancing/scaling requirements.
- Gemini API free tier is sufficient for expected demo call volume (see Architecture doc for provider details).

## 5. Constraints
- Backend: Python 3.11+, FastAPI.
- Frontend: Next.js (App Router) + TypeScript + Tailwind CSS.
- Database: PostgreSQL.
- No paid infrastructure required for MVP.
