# AI JobMatch — API Specification

## 1. Conventions
- Base URL (dev): `http://localhost:8000/api`
- All responses JSON. All requests/responses validated with Pydantic schemas.
- Session identified via httpOnly cookie `session_id`, set automatically on first request if absent (middleware).
- Errors follow a consistent shape:
```json
{
  "error": {
    "code": "INVALID_PDF",
    "message": "This resume appears to be a scanned image. Please upload a text-based PDF."
  }
}
```
- Standard HTTP status codes: 400 (validation), 404 (not found), 422 (schema validation failure), 500 (server error), 502/504 (upstream AI provider failure/timeout).

## 2. Endpoints

### 2.1 `POST /api/resumes`
Upload and parse a resume.
**Request**: `multipart/form-data`, field `file` (PDF, max 5MB).
**Response 201**:
```json
{
  "id": "uuid",
  "filename": "resume.pdf",
  "parsed_data": {
    "name": "string",
    "summary": "string",
    "education": [{"degree": "string", "institution": "string", "year": "string"}],
    "experience": [{"title": "string", "company": "string", "duration": "string", "description": "string", "type": "professional|internship|freelance|academic"}],
    "projects": [{"name": "string", "description": "string", "technologies": ["string"]}],
    "skills": ["string"],
    "certifications": ["string"]
  },
  "created_at": "iso8601"
}
```
**Errors**: `400 INVALID_FILE_TYPE`, `400 FILE_TOO_LARGE`, `422 SCANNED_PDF_UNSUPPORTED`, `502 EXTRACTION_FAILED`.

### 2.2 `GET /api/resumes/{id}`
Returns a previously parsed resume (session-scoped).
**Response 200**: same shape as 2.1 response. **Errors**: `404 NOT_FOUND`.

### 2.3 `POST /api/jobs`
Submit and parse a job description.
**Request**:
```json
{ "raw_text": "string (min 50 words)" }
```
**Response 201**:
```json
{
  "id": "uuid",
  "parsed_data": {
    "title": "string",
    "required_skills": ["string"],
    "preferred_skills": ["string"],
    "responsibilities": ["string"],
    "experience_years_required": 2,
    "education_requirement": "string"
  },
  "created_at": "iso8601"
}
```
**Errors**: `400 JD_TOO_SHORT`, `502 EXTRACTION_FAILED`.

### 2.4 `POST /api/analyze`
Run (or return cached) full matching analysis for a resume + job pair.
**Request**:
```json
{ "resume_id": "uuid", "job_id": "uuid" }
```
**Response 200/201** (201 if freshly computed, 200 if served from cache):
```json
{
  "id": "uuid",
  "resume_id": "uuid",
  "job_id": "uuid",
  "overall_score": 84.8,
  "sub_scores": {
    "skill_score": 91.2,
    "semantic_score": 88.0,
    "experience_score": 72.0,
    "education_score": 100.0,
    "project_evidence_score": 80.0
  },
  "matched_skills": [
    {"skill": "Python", "tier": "exact", "evidence": ["skills_section", "3 projects"]},
    {"skill": "PostgreSQL", "tier": "alias", "matched_as": "Postgres", "evidence": ["1 project"]}
  ],
  "missing_skills": [
    {"skill": "FastAPI", "required": true},
    {"skill": "AWS", "required": false}
  ],
  "related_skills": [
    {"skill": "FastAPI", "related_to": "Flask", "similarity": 0.78}
  ],
  "explanation": "string — plain-language summary grounded in the scores above",
  "recommendations": [
    {"type": "add_skill", "content": "string", "priority": 1}
  ],
  "cached": false,
  "created_at": "iso8601"
}
```
**Errors**: `404 RESUME_NOT_FOUND`, `404 JOB_NOT_FOUND`, `502 AI_PROVIDER_ERROR`, `504 AI_PROVIDER_TIMEOUT`.

### 2.5 `GET /api/analyses`
List past analyses for the current session.
**Query params**: `limit` (default 20), `offset` (default 0).
**Response 200**:
```json
{
  "items": [
    {"id": "uuid", "job_title": "string", "overall_score": 84.8, "created_at": "iso8601"}
  ],
  "total": 5
}
```

### 2.6 `GET /api/analyses/{id}`
Full detail for one past analysis — same shape as 2.4 response.
**Errors**: `404 NOT_FOUND`.

### 2.7 `GET /api/health`
Liveness check. **Response 200**: `{"status": "ok"}`.

## 3. Rate/Timeout Behavior
- Every outbound AI provider call: 30s timeout, 1 automatic retry on 5xx/timeout, then surface `502`/`504` to client.
- `POST /api/analyze` should target sub-15s response time under normal conditions (concurrent extraction calls per SRS NFR-2).

## 4. Notes for Claude Code
- Implement `/api/analyze` idempotently: hash-check `resumes.content_hash` + `jobs.content_hash` against existing `analyses` rows before doing any AI calls.
- Define all request/response schemas as Pydantic models in `backend/app/schemas/`, and reuse them for FastAPI's automatic OpenAPI docs (`/docs`) — this gives a free, always-accurate interactive API reference during development.
- Keep API routes thin — all logic delegated to `services/`.
