# AI JobMatch — Claude Code Prompts (Learning Edition)

Run these in order, one phase at a time, in a Claude Code session opened in the project root. Read `08-Learning-Guide.md` Part A once before Phase 0. Then for each phase: run the prompt, do the "explain it back" follow-up, do the verification, read that phase's Learning Guide section, then commit.

---

## First message (orientation — run once)
```
Read every file in /docs, including 08-Learning-Guide.md and this
prompts file. Give me a short summary of what we're building and
confirm you understand we'll work through 07-Development-Roadmap.md
one phase at a time. Also confirm you understand this: after each
phase, I'm going to ask you to explain what you built in plain
language, so write code with that in mind — clear naming, and be
ready to walk me through it, not just report "done." Don't start
building yet.
```

---

## Phase 0 — Environment & Scaffolding
```
Phase 0: Environment & Scaffolding from 07-Development-Roadmap.md.
Set up the full skeleton per 03-System-Architecture.md's folder
structure — Next.js+TypeScript+Tailwind frontend, FastAPI backend,
docker-compose.yml with Postgres, .env.example for both. Get
GET /api/health returning {"status":"ok"} and the Next.js home page
fetching and displaying it. Initialize git and Alembic with an empty
baseline migration.

I'm a beginner — as you build, briefly explain in comments or your
summary what each major file/folder is for. At the end, tell me the
exact commands to run to start everything myself.
```
**After it finishes:** *"Explain what docker-compose.yml is doing, line by line, like I've never seen one before."*
**Verify:** `docker-compose up` starts Postgres; backend and frontend run; home page shows "ok".
**Read:** Learning Guide → Phase 0 section.
**Commit:** `feat: initial project scaffolding (Phase 0)`

---

## Phase 1 — Database & Skill Taxonomy
```
Phase 1: Database & Skill Taxonomy. Implement all tables from
04-Database-Design.md as SQLAlchemy models with Alembic migrations.
Write scripts/seed_skills.py to populate the skills table with 100+
real tech skills and aliases. Add a basic repository layer for
resumes, jobs, and analyses.

Explain what a migration file actually contains and show me the raw
SQL Alembic generated for one of them, so I can see what's happening
underneath the ORM.
```
**Verify:** migrations run clean from empty DB; `skills` table populated.
**Read:** Learning Guide → Phase 1 section.
**Commit:** `feat: database models, migrations, skill taxonomy seed (Phase 1)`

---

## Phase 2 — Resume Parsing
```
Phase 2: Resume Parsing (no AI yet). Implement POST /api/resumes per
05-API-Specification.md — PyMuPDF text extraction, section-detection
heuristics, the scanned-PDF error case from FR-4 in 02-SRS.md.

Show me how to test this endpoint in Postman before we build any
frontend for it, and explain what each part of the Postman request
(method, body type, headers) needs to be set to.
```
**Verify:** upload a real resume PDF via Postman, get back extracted text/sections. Try a scanned PDF too — confirm the error case.
**Read:** Learning Guide → Phase 2 section.
**Commit:** `feat: resume PDF parsing and section detection (Phase 2)`

---

## Phase 3 — AI Extraction
```
Phase 3: Resume & JD Structured Extraction. Implement the AIService
from 03-System-Architecture.md wired to Gemini — I'll set
GEMINI_API_KEY in backend/.env myself, tell me the exact variable name
before you write the code that reads it. Implement extract_structured()
for ResumeProfile and JobProfile with the retry-on-validation-failure
behavior from FR-7. Implement POST /api/jobs. Update POST /api/resumes
to call structured extraction and store parsed_data.

Show me the actual prompt text you're sending to Gemini, and explain
why it's structured the way it is.
```
**Verify:** real resume/JD produce correctly populated JSON.
**Read:** Learning Guide → Phase 3 section.
**Commit:** `feat: LLM structured extraction for resume and job data (Phase 3)`

---

## Phase 4 — Skill Normalization
```
Phase 4: Skill Normalization. Implement the normalizer per
03-System-Architecture.md — exact match, then alias match, then
RapidFuzz fuzzy match, then free-text fallback. Populate resume_skills
and job_skills on extraction.

Show me a quick test proving "Postgres" and "PostgreSQL" normalize to
the same taxonomy entry, and explain which layer (exact/alias/fuzzy)
actually caught that specific case.
```
**Read:** Learning Guide → Phase 4 section.
**Commit:** `feat: skill taxonomy normalization (Phase 4)`

---

## Phase 5 — Matching Engine
```
Phase 5: Matching Engine. Implement local embeddings via
sentence-transformers, three-tier skill classification
(exact/alias/related) from FR-14, and all sub-score + weighted
overall_score calculations from 03-System-Architecture.md section 5 —
pure, deterministic Python, no LLM call. Write unit tests that don't
require any AI calls. Implement the content_hash caching check.

This is the most important part of the whole project for me to
understand. Walk me through the exact math for one example: given a
sample skill list, show me how the score gets computed step by step.
```
**Verify:** run the same resume+JD pair twice, confirm identical score. Run the new pytest tests.
**Read:** Learning Guide → Phase 5 section (this is the one to really sit with).
**Commit:** `feat: deterministic hybrid matching engine (Phase 5)` — consider doing this one on a branch (`git checkout -b feature/matching-engine`) and merging via a PR on GitHub, just to practice the workflow once.

---

## Phase 6 — Explanation & Full Analyze Endpoint
```
Phase 6: Explanation & Recommendations. Implement generate_explanation()
per FR-19/FR-20 — one Gemini call given only the computed scores and
skill lists as context, explicitly told not to alter the score or
invent achievements. Wire up POST /api/analyze per
05-API-Specification.md, with independent extraction calls running
concurrently via asyncio.gather.

Explain what asyncio.gather is actually doing here and roughly how
much time it's saving compared to running the calls one after another.
```
**Verify:** full `/api/analyze` call returns a coherent result within ~15s.
**Read:** Learning Guide → Phase 6 section.
**Commit:** `feat: explanation generation and full analyze endpoint (Phase 6)`

---

## Phase 7 — Frontend
```
Phase 7: Frontend Core Flow. Build /, /results/[id], and /history per
06-UI-UX.md sections 2-3, wired to the real backend — no mock data.
Implement all error/loading/empty states from section 5, including a
deliberately-broken test case (JD too short) so I can see the error
state render.

After it's working, open Chrome DevTools with me conceptually — tell
me what I should click on (Network tab) to watch the actual
POST /api/analyze request happen when I click the button.
```
**Verify:** complete the full flow yourself in the browser. Open DevTools → Network tab and actually watch the request fire.
**Read:** Learning Guide → Phase 7 section (the request-lifecycle walkthrough — practice saying it out loud).
**Commit:** `feat: frontend core flow — upload, results, history (Phase 7)`

---

## Phase 8 — Testing & Hardening
```
Phase 8: Testing & Hardening. Add pytest coverage prioritizing the
scoring engine, then API endpoint happy/error paths, then
normalization logic. Grep for any "ATS certified" language per NFR-8
and flag it. Confirm no AI provider key ends up in frontend code per
NFR-4.

Run the test suite and show me the output, and explain what each
failing test (if any) is actually telling us.
```
**Read:** Learning Guide → Phase 8 section.
**Commit:** `test: add scoring engine and API test coverage (Phase 8)`

---

## Phase 9 — Deployment
```
Phase 9: Deployment. Walk me through deploying backend to
Render/Railway, frontend to Vercel, database to Neon or Supabase.
Tell me exactly which env vars to set on each platform, in what order
to deploy so migrations run correctly, and what to click in each
dashboard — I haven't used any of these platforms before.
```
**You do manually:** create the Render/Railway, Neon/Supabase accounts; click through their dashboards as instructed.
**Read:** Learning Guide → Phase 9 section.
**Commit:** `chore: deployment configuration (Phase 9)`

---

## Phase 10 — Documentation
```
Phase 10: Documentation. Write README.md — what it does, the
architecture diagram from 03-System-Architecture.md, tech stack, how
to run locally, and a "key engineering decisions" section using the
Interview Q&A prep from 07-Development-Roadmap.md and
08-Learning-Guide.md.
```
**Read:** Learning Guide → Phase 10 section, then close the loop — try explaining the whole project out loud to yourself (or a friend) using only the README and your own memory, no notes.
**Commit:** `docs: README and project documentation (Phase 10)`

---

## Standing rule for every phase
If Claude Code starts building something outside the current phase's scope, say: *"That's a later phase — stop and stay inside what this phase asked for."* If you don't understand something it just did, stop and ask before moving to the next prompt — the goal is understanding at every step, not just a finished app at the end.
