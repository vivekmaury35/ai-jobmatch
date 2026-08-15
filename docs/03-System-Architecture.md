# AI JobMatch — System Architecture

## 1. High-Level Architecture (MVP)

```
┌─────────────────────────┐
│   Next.js Frontend       │
│  TypeScript + Tailwind   │
└────────────┬─────────────┘
             │ REST (JSON) over HTTPS
┌────────────▼─────────────┐
│      FastAPI Backend      │
│         Python 3.11       │
└──┬───────────┬───────────┬┘
   │           │           │
┌──▼───┐  ┌────▼─────┐ ┌───▼────────┐
│Resume │  │  Match    │ │  AI Service│
│Parser │  │  Engine   │ │  (Gemini)  │
│PyMuPDF│  │(rules +   │ │  + local   │
│       │  │embeddings)│ │  Sentence  │
│       │  │           │ │Transformers│
└──┬────┘  └────┬──────┘ └────┬───────┘
   │             │             │
   └─────────────┼─────────────┘
                 │
          ┌──────▼──────┐
          │ PostgreSQL  │
          └─────────────┘
```

**Key architectural decision vs. the earlier research:** the AI layer for MVP calls **Gemini API directly** (server-side, one HTTP client, one API key), not through a self-hosted OmniRoute gateway. OmniRoute is a real project, but it's a *local proxy you run yourself* (default `localhost:20128`) that aggregates provider accounts — it is not itself a hosted free-tier AI provider. Adding it as the primary dependency means keeping a second local service alive for every AI call, which is unnecessary infrastructure risk for an MVP. It's kept as an optional Phase-2 swap (see §7).

## 2. Component Responsibilities

| Component | Responsibility |
|---|---|
| Next.js Frontend | Upload UI, JD input, results display, history view. No business logic — calls backend REST API only. |
| FastAPI Backend | Orchestrates the whole pipeline: parsing, normalization, matching, AI calls, persistence. |
| Resume Parser | PDF → raw text (PyMuPDF) → section detection → passed to AI Service for structured extraction. |
| JD Analyzer | Raw JD text → passed to AI Service for structured extraction into `JobProfile`. |
| Skill Normalizer | Maps raw skill strings to canonical taxonomy entries (exact/alias) using a DB-backed dictionary + RapidFuzz for fuzzy matching. |
| Match Engine | Pure Python, deterministic. Computes skill/semantic/experience/education sub-scores and the weighted overall score. Does NOT call any AI provider. |
| AI Service | Thin abstraction (`generate()`, `extract_structured()`, `embed()`) wrapping Gemini API (LLM calls) and local Sentence Transformers (embeddings). Only this layer talks to external AI providers. |
| PostgreSQL | Stores resumes, jobs, skills taxonomy, analyses, and their results. |

## 3. AI Provider Abstraction

Even though MVP uses Gemini directly, structure the code behind an interface so swapping/adding providers later doesn't touch calling code:

```python
class AIService:
    async def extract_structured(self, text: str, schema: Type[BaseModel]) -> BaseModel: ...
    async def generate_explanation(self, context: dict) -> str: ...
    def embed(self, text: str) -> list[float]: ...  # local, sync, no network call
```

- `extract_structured` and `generate_explanation` → Gemini API (`google-generativeai` SDK or REST), server-side only.
- `embed` → local `sentence-transformers` model (e.g., `all-MiniLM-L6-v2`), no network call, no cost.

## 4. Data Flow (single analysis request)

1. Frontend uploads PDF + JD text → `POST /api/analyze`
2. Backend, concurrently (asyncio.gather):
   - Extracts resume text (PyMuPDF) → section detect → Gemini call → `ResumeProfile`
   - Sends JD text → Gemini call → `JobProfile`
3. Backend normalizes all skills against taxonomy.
4. Backend computes embeddings (local) for resume content blocks and JD requirement blocks.
5. Match Engine (pure Python, deterministic) computes sub-scores + overall score + matched/missing/related skill lists.
6. Backend makes ONE Gemini call for explanation + recommendations, passing only the computed scores/lists as context (not asking the LLM to invent a score).
7. Backend persists full result to PostgreSQL.
8. Backend returns JSON result to frontend.

Total external AI calls per analysis: **3** (resume extraction, JD extraction, explanation/recommendations). Embeddings are local and free.

## 5. Scoring Weights (deterministic, in code — not LLM-decided)

| Sub-score | Weight |
|---|---|
| Skill Match (exact/alias/related) | 35% |
| Semantic Similarity | 25% |
| Experience Match | 20% |
| Project Evidence | 10% |
| Education Match | 10% |

Skill match tier values: exact = 1.0, alias = 0.95, related (semantic > 0.75) = 0.5, missing = 0.0.

These weights live in one config constant (`app/core/scoring_config.py`) so they're easy to tune and easy to explain in an interview.

## 6. Technology Stack

| Layer | Technology |
|---|---|
| Frontend framework | Next.js 14+ (App Router) |
| Language | TypeScript |
| Styling | Tailwind CSS |
| Charts (Phase 2) | Recharts |
| Backend framework | FastAPI |
| Backend language | Python 3.11+ |
| Database | PostgreSQL |
| ORM | SQLAlchemy 2.x |
| Migrations | Alembic |
| PDF parsing | PyMuPDF (`fitz`) |
| Validation | Pydantic v2 |
| LLM | Google Gemini API (free tier) |
| Embeddings | `sentence-transformers` (local, `all-MiniLM-L6-v2`) |
| Fuzzy matching | RapidFuzz |
| HTTP client | httpx (async) |
| Backend testing | Pytest |
| Containerization | Docker Compose (Postgres at minimum) |

## 7. Optional Phase 2: Multi-Provider AI Gateway
If you want the "provider abstraction" resume line to be literally true, swap Gemini-direct for a self-hosted OmniRoute instance behind the same `AIService` interface — no other code changes needed, because the abstraction in §3 already isolates this. Not required for MVP; don't start here.

## 8. Folder Structure

```
ai-jobmatch/
├── frontend/
│   ├── app/
│   │   ├── page.tsx                # upload + JD input
│   │   ├── results/[id]/page.tsx   # analysis result view
│   │   └── history/page.tsx
│   ├── components/
│   ├── lib/
│   │   └── api.ts                  # typed fetch wrapper to backend
│   └── types/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── resumes.py
│   │   │   ├── jobs.py
│   │   │   └── analyses.py
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   └── scoring_config.py
│   │   ├── models/            # SQLAlchemy models
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── services/
│   │   │   ├── resume_parser/
│   │   │   ├── jd_analyzer/
│   │   │   ├── skill_normalizer/
│   │   │   ├── matching/
│   │   │   └── ai/             # AIService (Gemini + Sentence Transformers)
│   │   ├── repositories/
│   │   └── main.py
│   ├── migrations/
│   ├── tests/
│   └── requirements.txt
│
├── docs/                       # this document set
├── .env.example
├── docker-compose.yml
└── README.md
```

## 9. Security Notes
- All AI provider keys live in backend `.env`, never in frontend env vars.
- CORS on FastAPI restricted to the frontend's origin(s).
- File upload size-limited and type-validated server-side (not trusted from client).
- Session identifier (see SRS §2.6) stored as an httpOnly cookie, not exposed to JS.

## 10. Deployment (post-MVP)
- Frontend → Vercel
- Backend → Render or Railway (free/low tier)
- Database → managed free-tier Postgres (Neon, Supabase, or Render Postgres)
- Local dev uses Docker Compose for Postgres only; frontend/backend run natively for fast iteration.
