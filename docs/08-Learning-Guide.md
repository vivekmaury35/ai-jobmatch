# AI JobMatch — Learning Guide

## How to use this document
This is your companion while building with Claude Code. `09-Claude-Code-Prompts.md` has the exact prompts to run for each phase — each prompt ends by telling you which section of *this* file to read before or after. Don't read this front-to-back in one sitting; read each phase's section when you actually reach that phase. Concepts stick when they're attached to code you just watched get written, not before.

Every technology entry below follows the same shape: **What it is → Why we're using it here → What's happening behind the scenes → Alternatives & trade-offs → Commands you'll actually use → Interview Q&A.**

---

## Part A — Foundations (read before Phase 0)

### A.1 How to use Claude Code well (not just "prompt and accept")
Claude Code is an agent that reads your files, writes/edits code, and runs commands in your terminal. The temptation as a "copy-paster" is to paste a prompt, see it says "Done," and move on. That skips the entire point of doing this project. Instead:

- **After every phase, ask it to explain what it built** before you move on: *"Walk me through the files you just created and what each one does, like I'm new to this."* This is not optional — treat it as part of the prompt, not a follow-up you might skip.
- **Read the diff, even if you don't fully understand it.** Claude Code shows you what changed. Skim it. Ask about any function name or file you don't recognize.
- **Interrupt it if it's doing something you don't understand** — you can stop it mid-task and ask "wait, why are you doing that?" This is normal, not rude, and it's literally how you'll be expected to review AI-assisted code on a real team.
- **Ask it to explain errors instead of just fixing them silently** — when something breaks, say *"before you fix it, tell me what actually went wrong and why."*
- **Use it as a tutor, not just a builder** — you can ask it conceptual questions ("what is CORS and why did we just configure it?") in the same session, separate from build prompts.
- **Don't let it jump ahead** — this is why every phase prompt says "implement only this phase." Left alone, coding agents tend to over-deliver, which sounds nice but means you never got to absorb phase N before phase N+3 landed on top of it.

**Interview Q&A**
- *"How do you use AI coding tools in your workflow?"* → Something like: "I use it to accelerate implementation, but I review every change, ask it to explain decisions I don't understand, and I stay responsible for knowing why the code works — I don't ship what I can't explain."
- *"What's a risk of relying on AI-generated code?"* → It can be confidently wrong, it can introduce patterns you don't understand (so you can't debug them later), and it can silently skip edge cases unless you specifically ask it to handle them.

### A.2 Git & GitHub — the basics you'll actually use
**What it is:** Git is version control — it tracks every change to your code over time on your own machine. GitHub is a *hosting service* for Git repositories in the cloud, plus collaboration features (pull requests, issues, code review).

**Git vs GitHub, precisely:** Git works with zero internet connection — it's local history. GitHub is where you push that history so it's backed up, shareable, and reviewable. You could use Git without ever touching GitHub; you can't have a GitHub repo without Git underneath it.

**Why it matters for a fresher:** every company you'll interview at uses Git. Not knowing basic Git commands is one of the fastest ways to look inexperienced, regardless of how good your code is.

**Core commands you'll use constantly:**
| Command | What it does |
|---|---|
| `git init` | Turns the current folder into a Git repository (Claude Code will do this in Phase 0) |
| `git status` | Shows what's changed since your last commit — your most-used command |
| `git add <file>` or `git add .` | Stages changes (marks them "ready to commit") |
| `git commit -m "message"` | Saves a snapshot of staged changes with a description |
| `git log --oneline` | Shows commit history, compact |
| `git branch <name>` | Creates a new branch (an isolated line of work) |
| `git checkout <name>` / `git switch <name>` | Switches to a branch |
| `git checkout -b <name>` | Creates *and* switches to a new branch in one step |
| `git push` | Uploads your local commits to GitHub |
| `git pull` | Downloads and merges changes from GitHub into your local copy |
| `git diff` | Shows exact line-by-line changes not yet committed |
| `git clone <url>` | Downloads a full copy of a remote repo (how you'd start on a new team) |

**What is a commit, really?** A commit is a saved checkpoint — a snapshot of your entire project at that moment, with a message explaining what changed. Good commits are small and focused ("add resume upload endpoint," not "stuff"). You should commit after every phase passes its acceptance criteria — that gives you a clean rollback point if a later phase breaks something.

**What is a branch?** A separate, isolated line of development off your main codebase. In a real company: you'd create a branch per feature/bug (`feature/resume-upload`), do your work there without touching the stable `main` branch, then merge it back once it's reviewed. For this solo project, you can work mostly on `main` for simplicity, but I'll flag good moments to practice branching (e.g. before Phase 7's frontend work) so you've actually done it at least once.

**What is a Pull Request (PR)?** A GitHub feature — a request to merge one branch into another, with a diff view for reviewers to comment on before it's approved and merged. Even solo, opening a PR from a feature branch into `main` and reading your own diff there is good practice — it's literally what you'll do at a job.

**When should you commit in this project?** After each phase's acceptance criteria pass — not mid-phase, and not "whenever I remember." A commit message pattern that reads well in a portfolio history: `feat: add resume PDF parsing (Phase 2)`, `feat: implement deterministic matching engine (Phase 5)`, `fix: handle scanned PDF error case`.

**Interview Q&A**
- *"What's the difference between Git and GitHub?"* → Git is the version control tool itself (local); GitHub is a cloud platform for hosting Git repos and collaborating around them.
- *"What is a commit?"* → A snapshot of the project at a point in time, with a message describing the change.
- *"What's a branch, and why use one?"* → An isolated copy of the codebase for working on something without affecting the stable version until it's ready and reviewed.
- *"What's a pull request?"* → A proposal to merge one branch into another, reviewed via a diff before merging.
- *"Walk me through your Git workflow on this project."* → Be ready to actually describe what you did — commit-per-phase, meaningful messages, at least one branch/PR practiced.

### A.3 What is an API, actually?
**What it is:** An API (Application Programming Interface) is a defined way for one program to ask another program to do something or give it data, without needing to know how that other program works internally — just what to send and what you'll get back.

**In this project specifically:** your Next.js frontend doesn't touch the database or call Gemini directly — it sends an HTTP request to your FastAPI backend (e.g. `POST /api/analyze`), the backend does the real work, and sends back a JSON response. That boundary is the API.

**REST, specifically:** REST is a *style* of API design built on HTTP methods with specific meanings:
| Method | Meaning | Example in this project |
|---|---|---|
| `GET` | Read/fetch data | `GET /api/analyses/{id}` — fetch a past result |
| `POST` | Create something new | `POST /api/resumes` — upload a resume |
| `PUT`/`PATCH` | Update something existing | not heavily used in this MVP |
| `DELETE` | Remove something | not in this MVP |

**Status codes you'll see constantly:** `200` OK, `201` Created, `400` bad request (your fault, client-side), `404` not found, `422` validation failed, `500` server error (their fault, backend crashed), `502`/`504` upstream service (Gemini) failed or timed out.

**Postman:** a tool for manually sending API requests without needing a frontend — you'll use it in Phase 2–3 to test `POST /api/resumes` directly (upload a file, see the raw JSON response) before the frontend even exists. This is how backend developers routinely test their own work in isolation.

**Interview Q&A**
- *"What is an API?"* → A defined contract for how two systems exchange requests and data.
- *"What's the difference between GET and POST?"* → GET retrieves data and shouldn't change anything server-side; POST creates/submits data and does change state.
- *"How does your frontend talk to your backend?"* → Via REST API calls over HTTP — the frontend calls specific endpoints like `/api/analyze`, sends JSON, gets JSON back.
- *"What do you do when an API call fails?"* → Check the status code and error body, look at network logs (Chrome DevTools), reproduce with Postman to isolate frontend vs backend, check backend logs for the actual exception.

### A.4 Environment variables & `.env` — why secrets never live in code
**What it is:** Environment variables are configuration values (API keys, database URLs, secrets) supplied to your app at runtime instead of hardcoded in your source files. A `.env` file holds these locally, and is **never committed to Git** — it's listed in `.gitignore` for that exact reason. Committing a real `.env` with live keys to a public GitHub repo is one of the most common real-world security incidents for junior developers — bots scan public GitHub for exposed API keys within minutes of a push.

**Why:** if your `GEMINI_API_KEY` were hardcoded in a Python file and pushed to GitHub, anyone could copy it and run up your bill (or worse) on your account. `.env` keeps secrets out of your codebase entirely; `.env.example` (which *is* committed) shows what variables are needed, with placeholder/no values, so anyone cloning the repo knows what to configure.

**In this project:** `backend/.env` will hold `GEMINI_API_KEY` and your database connection string. `frontend/.env.local` (if needed) holds only non-secret, public-safe values — never an AI provider key, per NFR-4 in the SRS.

**Interview Q&A**
- *"How do you handle secrets/API keys in your projects?"* → Environment variables loaded from a `.env` file that's git-ignored, never hardcoded, never in frontend/client-side code.
- *"What's the difference between `.env` and `.env.example`?"* → `.env` has real secrets and is never committed; `.env.example` documents the required variable names with no real values, and is committed so others know what to set up.

---

## Part B — Phase-by-phase

### Phase 0 — Environment & Scaffolding

**New concepts this phase:**

**Docker & Docker Desktop**
- *What it is:* Docker packages an application (or in our case, just Postgres) along with everything it needs to run — into a "container" — so it behaves identically on any machine, regardless of what's installed on that machine's OS.
- *Why we're using it here:* Installing PostgreSQL natively on Windows is fiddly (services, PATH issues, version conflicts). Docker gives you a disposable, identical Postgres instance with one command, and it's exactly what a real backend team would do for local dev.
- *Behind the scenes:* Docker Desktop runs a lightweight Linux VM on Windows; your `docker-compose.yml` file describes what containers to run (here: just `postgres`) and how they're configured (port, credentials, volume for data persistence). `docker-compose up` reads that file and starts everything it describes.
- *Alternatives & trade-offs:* Install Postgres natively (more setup pain, but no Docker dependency) or use a free cloud Postgres from day one (Neon/Supabase — simpler locally, but you're dependent on internet access during dev, and it's less representative of how real local dev environments work).
- *Commands you'll use:*
  | Command | What it does |
  |---|---|
  | `docker --version` | Confirms Docker is installed |
  | `docker-compose up` | Starts the services defined in docker-compose.yml (foreground) |
  | `docker-compose up -d` | Same, but detached (runs in background) |
  | `docker-compose down` | Stops and removes the containers |
  | `docker ps` | Lists currently running containers |
  | `docker logs <container>` | Shows a container's logs (useful when Postgres won't start) |
- *Interview Q&A:*
  - *"What is Docker and why do developers use it?"* → It packages an app plus its dependencies into a portable container so "works on my machine" stops being a real problem — the same container runs identically in dev, CI, and production.
  - *"What's a container vs a virtual machine?"* → A VM virtualizes an entire OS; a container shares the host OS kernel and only isolates the application layer — much lighter weight and faster to start.
  - *"Why did you use Docker in this project specifically?"* → To get a consistent, disposable local Postgres instance without native install friction, matching how a real team would standardize dev environments.

**Next.js, TypeScript, Tailwind — quick orientation**
- *Next.js:* a React framework that adds routing, server-side rendering, and API conventions on top of plain React. "App Router" (what we're using) organizes pages by folder structure under `app/`.
- *TypeScript:* JavaScript with static types — catches a category of bugs (wrong data shape, typos in property names) at write-time instead of at runtime. Given you're a beginner, TypeScript errors will feel annoying at first — that's normal; they're catching real mistakes before they become bugs in the browser.
- *Tailwind CSS:* a utility-class CSS framework — instead of writing custom CSS files, you compose styles directly in your markup (`className="flex items-center gap-4"`). Faster for solo devs, more verbose-looking markup.
- *Alternatives:* plain React + Vite (lighter, no built-in routing/SSR), CSS Modules or styled-components instead of Tailwind (more separation of concerns, more files to manage).

**FastAPI — quick orientation**
- *What it is:* a modern Python web framework specifically for building APIs, built on top of `Starlette` and `Pydantic`.
- *Why here:* automatic request/response validation via Pydantic, automatic interactive API docs at `/docs` (you'll see this — it's genuinely useful, not a gimmick), native async support (important for the concurrent AI calls in Phase 6), and it's the natural fit for Python's ML/NLP ecosystem (PyMuPDF, sentence-transformers).
- *Alternatives:* Flask (older, more manual, no built-in validation/docs), Django (heavier, batteries-included, overkill for an API-only backend), Node/Express (would mean two languages across the stack instead of one for backend logic + AI/NLP work).

**Git checkpoint for this phase:** once `docker-compose up` works and the health check renders, that's your first commit: `feat: initial project scaffolding (Phase 0)`.

---

### Phase 1 — Database & Skill Taxonomy

**New concepts:**

**What is a relational database, briefly**
- Data stored in tables with defined columns and types, with relationships between tables enforced by foreign keys (e.g. `resume_skills.resume_id` must point to a real row in `resumes`). This is *why* we chose Postgres over something like MongoDB — our data (resumes, jobs, skills, analyses) is naturally relational, with real many-to-many relationships (a resume has many skills, a skill appears across many resumes).
- *Alternatives:* MongoDB/NoSQL (better for unstructured/flexible-schema data, worse for enforcing the kind of structured relationships this app actually needs), SQLite (fine for prototyping, weaker for concurrent access and not what you'd deploy to production).

**ORM (SQLAlchemy) — what it actually does**
- *What it is:* an Object-Relational Mapper — lets you define database tables as Python classes and query them with Python instead of writing raw SQL strings everywhere.
- *Why:* type safety, less repetitive SQL, easier to reason about relationships in code. You'll still benefit from understanding what SQL it's generating underneath — ask Claude Code to show you the raw SQL for a query occasionally so it's not a total black box.
- *Alternatives:* raw SQL with a driver like `psycopg2` (more control, more boilerplate, more room for injection bugs if done carelessly), a lighter query builder.

**Migrations (Alembic) — what and why**
- *What it is:* a system for versioning changes to your database schema over time, the same way Git versions your code.
- *Why it matters:* without migrations, "add a column" means manually running SQL on every environment (your laptop, staging, production) and hoping you didn't forget one. Alembic generates a script for each schema change so you (or a deploy pipeline) can run `alembic upgrade head` anywhere and land on the exact same schema.
- *Commands:* `alembic revision --autogenerate -m "message"` (creates a migration file from your model changes), `alembic upgrade head` (applies all pending migrations).

**Interview Q&A**
- *"Why did you choose PostgreSQL over MongoDB?"* → The data is genuinely relational — resumes, jobs, skills, and analyses have real foreign-key relationships and benefit from enforced structure and joins, which a relational database is built for.
- *"What's an ORM, and what's the trade-off of using one?"* → It maps database tables to code objects, speeding up development and reducing raw SQL — the trade-off is an abstraction layer that can hide inefficient queries if you never look underneath it.
- *"What are database migrations and why do they matter?"* → Version-controlled, repeatable schema changes — without them, keeping dev/staging/production databases in sync becomes manual and error-prone.

**Git checkpoint:** `feat: database models, migrations, skill taxonomy seed (Phase 1)`.

---

### Phase 2 — Resume Parsing

**New concepts:**

**PyMuPDF & why PDF text extraction isn't trivial**
- PDFs don't store text like a Word doc — they store positioned drawing instructions. PyMuPDF (`fitz`) reads those instructions and reconstructs readable text. This is why scanned/image-based PDFs fail (there's no text to extract at all — just an image) — which is exactly the case FR-4 handles.

**Try this in Postman:** once `POST /api/resumes` exists, manually upload a real PDF via Postman before the frontend exists. This is the actual backend-dev workflow — test the API in isolation first.

**Interview Q&A**
- *"How does your app handle a scanned resume?"* → Detects it via extracted-text length below a threshold and returns a clear error instead of silently producing garbage output — OCR is explicitly out of scope, documented as a known limitation.
- *"What would you improve about resume parsing if you had more time?"* → Add OCR (Tesseract) for scanned PDFs, DOCX support, more robust section-detection beyond heading heuristics.

**Git checkpoint:** `feat: resume PDF parsing and section detection (Phase 2)`.

---

### Phase 3 — AI Extraction (LLMs, Gemini API)

**New concepts:**

**What is an LLM API call, actually?**
- You send a prompt (text) plus configuration (model name, parameters) as JSON to an HTTP endpoint; you get back JSON containing generated text. That's it — the "magic" is entirely inside the provider's model; your code is just an HTTP client with a well-crafted prompt.

**Structured output / schema-constrained extraction**
- *The problem:* LLMs generate free text by default — unreliable for code that needs `job_title` in a specific field every time.
- *The fix here:* Pydantic schemas define exactly what shape the response must have (`ResumeProfile`, `JobProfile`); the prompt instructs the model to return matching JSON; the response is validated against the schema, and re-requested on failure (FR-7). This is a core "AI engineering" pattern worth understanding deeply — it's very interview-relevant right now.

**Why Gemini over other LLM providers here:** free tier sufficient for a portfolio project, good structured-output support, no local GPU needed (unlike self-hosting a model). Alternatives: OpenAI API (paid, no meaningful free tier), Groq (extremely fast, smaller free limits, good for latency-sensitive steps), local open-source models via Ollama (free, no internet dependency, but requires real hardware and setup — heavier lift for this stage).

**Interview Q&A**
- *"How do you get reliable structured output from an LLM?"* → Define a strict schema (Pydantic), instruct the model explicitly to conform to it, validate the response, and retry with an error-correction prompt on failure rather than trusting free-form output.
- *"Why Gemini specifically?"* → Free tier fit the project's zero-budget constraint, with solid structured-output support — swappable later since the AI calls sit behind one internal interface (see Phase 6 / Architecture doc).
- *"What happens if the AI provider is down or times out?"* → A 30-second timeout, one automatic retry, then a clear `502`/`504` error surfaced to the user instead of an indefinite hang (FR-24/25).

**Git checkpoint:** `feat: LLM structured extraction for resume and job data (Phase 3)`.

---

### Phase 4 — Skill Normalization

**New concept: fuzzy matching (RapidFuzz)**
- *What it is:* string-similarity matching that tolerates typos/near-matches ("Postgre SQL" vs "PostgreSQL") using edit-distance-style algorithms, distinct from exact string equality or true semantic (meaning-based) similarity.
- *Where it sits in the pipeline:* exact match first (fastest, most certain) → alias-table match → fuzzy match (catches near-misses the alias table didn't anticipate) → semantic embedding similarity as the last resort (Phase 5) for genuinely different-but-related skills.

**Interview Q&A**
- *"How do you handle the same skill written differently across resumes/JDs?"* → A layered approach: exact match, then a curated alias table, then fuzzy string matching, then semantic similarity as a fallback — cheapest/most-certain methods tried first.

**Git checkpoint:** `feat: skill taxonomy normalization (Phase 4)`.

---

### Phase 5 — Matching Engine (the core of the project)

**New concepts:**

**Embeddings, explained simply**
- *What it is:* a way of converting text into a list of numbers (a vector) that captures its *meaning*, such that texts with similar meaning end up as nearby vectors — even without sharing exact words.
- *Why local (Sentence Transformers) instead of an API:* zero marginal cost, no network dependency, and this task doesn't need frontier-model quality — a small, well-established embedding model running on your own machine (or server) is genuinely the right tool here, not a compromise.
- *Cosine similarity:* the actual math used to compare two vectors — measures the angle between them (not their length), producing a score from -1 to 1 (in practice, usually 0 to 1 for this kind of text) where closer to 1 means "more similar in meaning."

**Why the score is computed in plain Python, not by the LLM — the single most important design decision in this project**
- Determinism (same input → same output, every time), explainability (you can point at the exact line of code that produced a number), resistance to prompt-injection-style gaming, and reproducibility for testing. This is your strongest, most specific interview talking point — know it cold.

**Interview Q&A**
- *"Explain how your matching score is calculated."* → Be ready to actually walk through: skill tiers (exact/alias/related/missing) → weighted sub-scores → fixed weighted sum → one number, entirely in deterministic code, with the LLM only used earlier for extraction and later for explaining the number in words.
- *"What are embeddings, and why do you need them here?"* → Numeric representations of text meaning, letting the system recognize that "built REST APIs in Python" and "developed FastAPI backend services" are related even with zero overlapping words.
- *"Why not just ask the LLM to score the match directly?"* → Non-deterministic across runs, not explainable, and easy to unintentionally (or intentionally) game — the score needs to be something you can defend as engineering, not an opaque model output.

**Git checkpoint:** `feat: deterministic hybrid matching engine (Phase 5)` — this is a good moment to actually practice a branch/PR (see Part A.2) since it's the most substantial single piece of logic in the app.

---

### Phase 6 — Explanation, Recommendations & the full `/api/analyze` endpoint

**New concept: `asyncio.gather` / concurrency, briefly**
- *The problem:* if resume extraction and JD extraction each take ~3 seconds and run one after another, that's 6 seconds wasted on work that doesn't depend on each other.
- *The fix:* `asyncio.gather` runs both async calls concurrently — the wait time overlaps instead of stacking, cutting real latency roughly in half for that step. This is a genuinely good "what happens behind the scenes" thing to be able to explain.

**Interview Q&A**
- *"How did you optimize latency in your pipeline?"* → Ran independent AI extraction calls concurrently via `asyncio.gather` instead of sequentially, cached repeat analyses by content hash, and kept embeddings local instead of another network round-trip.
- *"How do you prevent the AI from fabricating resume achievements in its suggestions?"* → The prompt explicitly restricts it to reasoning over the already-extracted, already-verified resume content — it's not asked to generate new claims about the candidate.

**Git checkpoint:** `feat: explanation generation and full analyze endpoint (Phase 6)`.

---

### Phase 7 — Frontend

**New concepts:**

**Chrome DevTools — your most-used debugging tool from here on**
- **Elements tab:** inspect the live DOM, edit CSS live to test a fix before writing it.
- **Console tab:** see `console.log` output and JS errors — your first stop when something looks visually broken.
- **Network tab:** see every API call your frontend makes — status code, request payload, response body, timing. This is *exactly* how you'll debug "why isn't my data showing up" — check whether the request even fired, what it sent, and what came back, before assuming the bug is in your React code.
- Right-click any page element → "Inspect" opens DevTools focused there.

**How a click actually becomes a database row — the full request lifecycle (know this cold for interviews):**
1. User clicks "Analyze" → React event handler fires.
2. Frontend calls `fetch('/api/analyze', {...})` — an HTTP POST with JSON body.
3. Request travels over the network to the FastAPI backend.
4. FastAPI's router matches the URL/method, validates the request body against a Pydantic schema.
5. The endpoint function runs — calls services (matching engine, AI service).
6. SQLAlchemy issues SQL to Postgres to persist the result.
7. FastAPI serializes the result to JSON and returns an HTTP response.
8. Frontend receives it, updates React state, the UI re-renders with the result.

Be able to say this out loud without notes — it's one of the single most common "explain your app" interview moments.

**Interview Q&A**
- *"Walk me through what happens when a user clicks your analyze button."* → Use the 8-step flow above, in your own words.
- *"How do you debug a frontend issue?"* → Start with the Network tab to confirm the request/response shape, Console for JS errors, then trace into React state/props if the data's correct but not rendering right.

**Git checkpoint:** `feat: frontend core flow — upload, results, history (Phase 7)`.

---

### Phase 8 — Testing & Hardening

**New concepts:**

**Why test the scoring engine specifically, first**
- It's pure, deterministic Python with no external dependencies (no AI calls, no database) — the cheapest, fastest, most reliable thing to test, and the part of the app whose correctness matters most. This is the standard "test pyramid" idea: more tests on cheap/fast/isolated logic, fewer on slow/expensive integration paths.

**Pytest basics**
- A test file lives near what it tests (`tests/test_scoring.py`), functions prefixed `test_`, `assert` statements check expected vs actual. Run with `pytest` from the backend folder.

**Interview Q&A**
- *"How did you test this project?"* → Unit tests on the deterministic scoring engine first (highest value, no external dependencies), then API endpoint tests for happy-path and key error cases.
- *"What's the difference between unit and integration tests?"* → Unit tests isolate one function/module with no external dependencies (fast, cheap); integration tests exercise multiple pieces together (e.g. a full API call hitting the real database) — slower, but catch issues unit tests can't.

**Git checkpoint:** `test: add scoring engine and API test coverage (Phase 8)`.

---

### Phase 9 — Deployment

**New concepts:**

**What "deployment" actually means**
- Taking code that runs on your laptop and making it run on a server reachable from the public internet, with real environment variables configured on that server (not your local `.env`), and a real database it can reach.

**Why Vercel for frontend, Render/Railway for backend — the actual reasoning**
- Vercel is purpose-built for Next.js (made by the same company) — near-zero-config deploys, automatic builds on every Git push.
- FastAPI needs a persistent Python process (not a great fit for Vercel's serverless-first model) — Render/Railway run a standard container/process, which fits a FastAPI + Postgres backend better.
- This is a real, common pattern: **different parts of a stack often deploy to different platforms suited to what they are** — not a compromise, a deliberate choice.

**CI/CD, briefly (you won't build this, but should be able to talk about it):** Continuous Integration/Continuous Deployment — automatically running tests and deploying on every push to `main`, instead of manually deploying by hand. Vercel already does a lightweight version of this automatically (deploy-on-push). Worth naming as a "what I'd add with more time" answer.

**Interview Q&A**
- *"How did you deploy this application?"* → Frontend on Vercel (native Next.js fit, deploy-on-push), backend on Render/Railway (needs a persistent Python process, not serverless), database on a managed free-tier Postgres (Neon/Supabase) — environment variables configured per-platform, never committed to the repo.
- *"What would you add for a production-grade deployment?"* → CI/CD pipeline running tests before deploy, monitoring/alerting, a staging environment separate from production, rate limiting.

**Git checkpoint:** `chore: deployment configuration (Phase 9)`.

---

### Phase 10 — Documentation & Presentation

**New concept: what a good README actually communicates**
A hiring-relevant README isn't just "how to run this" — it shows you understand *why* you built it this way. Structure: what it does → architecture diagram → key engineering decisions (deterministic scoring, provider abstraction, etc.) → how to run locally → what you'd improve with more time. That last section matters — it signals self-awareness, which interviewers specifically listen for.

**Final interview prep — the big-picture questions, now that you've built it:**
- *"What would you improve if you had more time?"* → Have 2–3 honest answers ready (OCR support, caching UI, real auth) — this is your Phase 2/deferred-features list from the PRD, verbatim.
- *"What are the limitations of your architecture?"* → Single-session (no real multi-user accounts), no horizontal scaling considered, free-tier AI rate limits, PDF-only resume support.
- *"How would you scale this application?"* → Move session data to real auth/accounts, add a job queue for AI calls instead of synchronous request-time calls, add caching at the infrastructure level, consider a managed vector database if embedding volume grew significantly.
- *"What security considerations did you account for?"* → Server-side-only API keys, input validation on file uploads (size/type), no secrets in frontend bundles, CORS restricted to known origins.

---

## Quick reference: full command cheat-sheet
```
# Git
git status / git add . / git commit -m "msg" / git push / git pull
git checkout -b feature/name

# Docker
docker-compose up -d / docker-compose down / docker ps / docker logs <name>

# Backend (from /backend)
pip install -r requirements.txt
uvicorn app.main:app --reload
alembic revision --autogenerate -m "msg"
alembic upgrade head
pytest

# Frontend (from /frontend)
npm install
npm run dev
```
