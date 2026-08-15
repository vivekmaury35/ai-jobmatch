# AI JobMatch — Development Roadmap

## How to use this doc with Claude Code
Work one phase at a time. At the start of each phase, point Claude Code at this whole `/docs` folder and say something like: *"Read all files in /docs. We're now starting Phase N: <name>. Implement only what's described for this phase. Don't build ahead into later phases."* Verify the acceptance criteria before moving on. This prevents Claude Code from sprawling into half-finished features across the whole app at once.

---

## Phase 0 — Environment & Scaffolding
**Goal**: empty-but-running skeleton, nothing functional yet.
- Create `frontend/` (Next.js + TypeScript + Tailwind) and `backend/` (FastAPI) per the folder structure in `03-System-Architecture.md`.
- `docker-compose.yml` with a Postgres service.
- `.env.example` for both frontend and backend (no real keys committed).
- FastAPI `GET /api/health` returns `{"status": "ok"}`.
- Next.js home page fetches `/api/health` and displays the status, proving frontend↔backend wiring.
- Alembic initialized with an empty baseline migration.

**Acceptance criteria**: `docker-compose up` starts Postgres; backend and frontend run locally; home page shows "ok" from the backend.

## Phase 1 — Database & Skill Taxonomy
- Implement all tables from `04-Database-Design.md` as SQLAlchemy models + Alembic migrations.
- Write and run `scripts/seed_skills.py` to populate ≥100 taxonomy entries with aliases.
- Basic repository layer for CRUD on `resumes`, `jobs`, `analyses`.

**Acceptance criteria**: migrations run clean from empty DB; `skills` table populated and queryable; can insert/read a dummy resume row via a test script.

## Phase 2 — Resume Parsing (no AI yet)
- `POST /api/resumes` accepts PDF, extracts raw text with PyMuPDF, runs section-detection heuristics, stores `raw_text` + `content_hash`.
- Handle the scanned-PDF case per FR-4 (short-text threshold → error).
- Test against 5+ real, varied resumes (different formats/lengths).

**Acceptance criteria**: uploading a real resume returns extracted raw text and detected section boundaries; a scanned/image PDF returns the correct error, not a crash.

## Phase 3 — Resume & JD Structured Extraction (AI Service, LLM)
- Implement `AIService` per `03-System-Architecture.md` §3, wired to Gemini API (server-side key from `.env`).
- Implement `extract_structured()` for `ResumeProfile` and `JobProfile` schemas, with the retry-on-validation-failure behavior from FR-7.
- `POST /api/jobs` implemented per API spec (min-length validation, structured extraction, persistence).
- Update `POST /api/resumes` to call structured extraction and store `parsed_data`.

**Acceptance criteria**: real resume → correctly populated `ResumeProfile` JSON; real JD → correctly populated `JobProfile` JSON; malformed LLM output triggers the retry path (test by temporarily forcing a bad prompt).

## Phase 4 — Skill Normalization
- Implement normalizer: exact taxonomy match → alias match (via `aliases` array) → fuzzy match (RapidFuzz) → fallback to free-text.
- Populate `resume_skills` and `job_skills` join tables on extraction.

**Acceptance criteria**: "Postgres" in a resume correctly normalizes to the same taxonomy entry as "PostgreSQL" in a JD.

## Phase 5 — Matching Engine (deterministic scoring)
- Implement local embeddings via `sentence-transformers`.
- Implement three-tier skill classification (exact/alias/related) per FR-14.
- Implement all sub-score calculations and the weighted `overall_score` per `03-System-Architecture.md` §5 — pure, deterministic Python, unit-tested.
- Implement the caching check (content_hash lookup) before running a fresh analysis.

**Acceptance criteria**: running the same resume+JD pair twice produces the identical overall_score; a unit test suite covers the scoring function directly (no AI calls needed to test this layer).

## Phase 6 — Explanation & Recommendations (AI Service, second LLM step)
- Implement `generate_explanation()` — single Gemini call, given only computed scores/lists as context, per FR-19/FR-20.
- Implement `POST /api/analyze` end-to-end per `05-API-Specification.md` §2.4.
- Add concurrency (asyncio.gather) for the independent extraction calls per NFR-2.

**Acceptance criteria**: full `/api/analyze` call on a real resume+JD returns a complete, coherent, non-fabricated explanation and recommendation set within ~15s.

## Phase 7 — Frontend: Core Flow
- Build `/`, `/results/[id]`, `/history` pages and components per `06-UI-UX.md` §2–3.
- Wire to the real backend API (no mock data).
- Implement all error/empty/loading states from `06-UI-UX.md` §5.

**Acceptance criteria**: a person can complete the full flow (upload → paste JD → analyze → see results → see it in history) using only the UI, with real backend calls, including at least one deliberately-triggered error case (e.g. JD too short) displaying correctly.

## Phase 8 — Testing & Hardening
- Backend: Pytest coverage for scoring engine (Phase 5, pure functions — highest priority), API endpoints (happy path + key error paths), normalization logic.
- Manual test pass with 5–10 varied real resumes × 3–5 varied real JDs.
- Verify NFR-4 (no keys in frontend bundle) and NFR-8 (no "ATS certified" language anywhere in copy).

**Acceptance criteria**: test suite passes; manual test matrix produces sane, explainable scores across all combinations; no security/copy violations found.

## Phase 9 — Deployment
- Deploy backend (Render/Railway free tier), frontend (Vercel), database (managed free-tier Postgres).
- Confirm CORS, env vars, and production DB migrations all work end-to-end on the deployed URL.

**Acceptance criteria**: the live public URL runs the full flow successfully with a real resume upload.

## Phase 10 — Documentation & Presentation
- Write `README.md`: what it does, architecture diagram, tech stack, how to run locally, key engineering decisions (deterministic scoring vs. LLM-scored, why Gemini-direct over OmniRoute for MVP, etc.)
- Prepare the LinkedIn/portfolio description using the framing from the interview Q&A in this doc set (see below).

**Acceptance criteria**: someone unfamiliar with the project could read the README and understand what was built and why, without asking follow-up questions.

---

## Explicitly Deferred to Phase 2 of the Product (post-launch, not part of the roadmap above)
Radar chart, Skill Gap Matrix, Evidence drill-down, ATS keyword report, Resume Quality Score, Recruiter Summary, analysis result caching UI, OmniRoute multi-provider swap-in, DOCX support, OCR for scanned PDFs, cover letter generation, interview-prep generation.

Build these only after Phases 0–10 above are fully working — resist the temptation to pull any of these forward.

## Interview Q&A Prep (for after it's built)
- **Why FastAPI over Node/Express?** Python ecosystem for NLP/document processing (PyMuPDF, sentence-transformers, spaCy) outweighs a unified-JS-stack convenience.
- **Why not let the LLM produce the score directly?** Non-deterministic, not reproducible, not explainable, easy to game — the score has to trace to code you can point at.
- **Why local embeddings instead of an embedding API?** Zero marginal cost, no added external dependency for a step that doesn't need frontier-model quality.
- **How do you avoid hallucinated resume "improvements"?** Prompt explicitly forbids fabrication; recommendations are generated only from extracted resume content passed as context, not free generation.
- **Why Gemini over OmniRoute for the AI layer?** OmniRoute is a self-hosted local gateway, not a hosted provider — adding it means keeping a second local service alive for every request. The `AIService` abstraction keeps that swap available later without being a Day-1 dependency.
