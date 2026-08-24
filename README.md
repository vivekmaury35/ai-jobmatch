# 🎯 AI JobMatch — Intelligent Resume & JD Analysis Platform

**AI JobMatch** is an advanced, AI-powered resume and job description (JD) matching system designed to give candidates instant, deep insights into how well their resume matches a specific job role. It provides multi-tier skill matching, ATS sub-score breakdowns, gap analysis, and tailored AI recommendations to optimize job applications.

---

## ✨ Features

- **📄 Smart Resume Parsing**: Extracts structured text and technical skills from PDF resumes using PyMuPDF and NLP normalization.
- **🤖 Dual-Engine Matching**:
  - **Deterministic Normalization Engine**: Matches exact skills, acronyms, and variations.
  - **LLM-Powered Semantic Analysis**: Evaluates experience depth, project evidence, soft skills, and AI tool usage (ChatGPT, Claude, Cursor AI, GitHub Copilot).
- **📊 Comprehensive ATS Sub-Scores**:
  - Overall Compatibility Score (0 - 100%)
  - Skill Score
  - Semantic Relevance Score
  - Experience Alignment
  - Project Evidence Score
  - Soft Skills & AI Tools Evaluation
- **💡 Actionable Feedback**: Highlights exact skill matches, missing requirements, and provides priority-ranked recommendations for resume improvements and interview preparation.
- **🕒 Application History**: Saved candidate analyses with instant re-visitation of historical match scores.

---

## 🛠️ Tech Stack

### **Frontend**
- **Framework**: [Next.js 16](https://nextjs.org/) (App Router, React 19)
- **Language**: TypeScript
- **Styling**: Vanilla CSS / Tailwind CSS, Dynamic Motion Animations
- **Icons**: Lucide React

### **Backend**
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+)
- **Database**: PostgreSQL with SQLAlchemy & Alembic Migrations
- **AI Services**: Google Gemini API (`google-genai`), PyMuPDF, Sentence Transformers, Scikit-learn
- **Task Runner / Server**: Uvicorn, Asyncio

---

## 📁 Repository Structure

```text
ai-jobmatch/
├── backend/
│   ├── app/
│   │   ├── api/            # FastAPI Route Handlers (Resumes, Jobs, Analyze)
│   │   ├── core/           # Configuration & Scoring Parameters
│   │   ├── models/         # SQLAlchemy DB Models
│   │   ├── schemas/        # Pydantic Input/Output Schemas
│   │   └── services/       # AI Engine, Matching Logic, Skill Normalization
│   ├── migrations/         # Alembic DB Migrations
│   ├── tests/              # Pytest Unit & Integration Tests
│   ├── requirements.txt    # Python Dependencies
│   └── .env.example        # Environment Variables Template
├── frontend/
│   ├── app/                # Next.js Pages & UI Components
│   ├── public/             # Static Assets
│   └── package.json        # Frontend Dependencies
├── docker-compose.yml      # Local PostgreSQL Setup
└── README.md               # Project Documentation
```

---

## 🔒 Security & Environment Variables

> ⚠️ **IMPORTANT**: Never commit your `.env` files or API keys to GitHub! The project `.gitignore` is pre-configured to keep secret files safe.

### Backend `.env` Setup
Create a file named `.env` inside the `backend/` directory:

```env
# Backend Configuration
PORT=8000
ENVIRONMENT=development

# Database Configuration (PostgreSQL)
DATABASE_URL=postgresql+psycopg2://jobmatch:password123@127.0.0.1:5432/jobmatch_db

# AI Provider Configuration ("gemini" or "openrouter")
AI_PROVIDER=gemini
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
```

### Frontend `.env.local` Setup
Create a file named `.env.local` inside the `frontend/` directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## 🚀 Local Development Setup

### Prerequisites
- Node.js (v18+)
- Python (3.11+)
- PostgreSQL (or Docker Desktop)

### 1. Database Setup (Docker)
```bash
docker-compose up -d
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv

# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

---

## 🌐 Production Deployment Guide

| Component | Recommended Platform | Setup Time |
| :--- | :--- | :--- |
| **Frontend** | [Vercel](https://vercel.com) | 2 Mins |
| **Backend** | [Render](https://render.com) or [Railway](https://railway.app) | 10 Mins |
| **Database** | [Neon.tech](https://neon.tech) (PostgreSQL) | 3 Mins |

1. **Database**: Create a free PostgreSQL instance on **Neon.tech** and copy the connection string.
2. **Backend (Render)**: Deploy `backend/` as a Python Web Service. Set environment variables (`DATABASE_URL`, `GEMINI_API_KEY`, `AI_PROVIDER=gemini`).
3. **Frontend (Vercel)**: Import `frontend/` repository on Vercel. Set `NEXT_PUBLIC_API_URL` to your live Render backend URL.

---

## 📄 License
This project is licensed under the MIT License.
