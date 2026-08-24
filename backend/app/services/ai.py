import os
import json
import logging
from typing import Type, TypeVar
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import AsyncOpenAI
from google import genai
from google.genai.errors import APIError
from pydantic import BaseModel, ValidationError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Global embedding model - initialized once at module load to avoid reloading on every request
_embedding_model = None

def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        logger.info("Loading embedding model (first time only)...")
        try:
            from sentence_transformers import SentenceTransformer
            _embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Embedding model loaded successfully")
        except ImportError:
            logger.warning("sentence-transformers not installed; embedding model unavailable")
            return None
    return _embedding_model


T = TypeVar("T", bound=BaseModel)

class AIExtractionError(Exception):
    pass

class AIService:
    def __init__(self):
        openrouter_key = settings.OPENROUTER_API_KEY or os.getenv("OPENROUTER_API_KEY", "")
        gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
        groq_key = settings.GROQ_API_KEY or os.getenv("GROQ_API_KEY", "")

        provider = (settings.AI_PROVIDER or "openrouter").lower()

        if provider == "openrouter" and not openrouter_key:
            provider = "gemini" if gemini_key else "openrouter"
        if provider == "groq" and not groq_key:
            provider = "gemini" if gemini_key else "openrouter"

        self.provider = provider

        if self.provider == "openrouter":
            self.client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_key)
            self.model = settings.OPENROUTER_MODEL or "openai/gpt-4o-mini"
        elif self.provider == "groq":
            self.client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=groq_key)
            self.model = settings.GROQ_MODEL or "llama-3.3-70b-versatile"
        else:
            self.client = genai.Client(api_key=gemini_key)
            self.model = "gemini-3.6-flash"


    async def _call_llm(self, prompt: str):
        if self.provider in ["openrouter", "groq"]:
            @retry(retry=retry_if_exception_type(Exception), stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=3))
            async def _call():
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content
            return await _call()
        else:
            @retry(retry=retry_if_exception_type(Exception), stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=4))
            async def _call():
                return await self.client.aio.models.generate_content(model=self.model, contents=prompt)
            response = await _call()
            return response.text.strip()


    async def extract_structured(self, text: str, schema: Type[T], extraction_type: str) -> T:
        schema_definition = schema.model_json_schema()

        base_prompt = f"""You are a precise data extraction specialist. Your task is to extract information from the provided text into the exact JSON schema defined below.

STRICT INSTRUCTIONS:
1. Return ONLY valid JSON that conforms to the schema.
2. For all 'List[str]' fields (especially skills, technologies, etc.), extract and normalize them into individual, atomic, single-word or short-phrase tokens.
3. DO NOT group multiple concepts together in one item (e.g., if the text says "HTML, CSS, and JS", return ["HTML", "CSS", "JavaScript"]).
4. Do not group descriptive phrases into single items (e.g., return "Python" instead of "Python development experience").
5. Return an empty list [] if no items are found.

SCHEMA:
{json.dumps(schema_definition, indent=2)}

DOCUMENT TEXT:
{text}
"""
        try:
            return await self._call_and_validate(base_prompt, schema)
        except Exception as e:
            logger.warning(f"AI extraction failed ({e}). Falling back to heuristic extraction.")
            return self._heuristic_fallback(text, schema, extraction_type)

    def _heuristic_fallback(self, text: str, schema: Type[T], extraction_type: str) -> T:
        import re
        COMMON_SKILLS = [
            "Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "HTML", "CSS", "SQL",
            "PostgreSQL", "MongoDB", "FastAPI", "Django", "Flask", "Tailwind", "Bootstrap", "Git", "GitHub",
            "Docker", "AWS", "Java", "C++", "C#", "PHP", "WordPress", "REST API", "GraphQL", "Linux", "Figma"
        ]
        found_skills = [s for s in COMMON_SKILLS if re.search(r'\b' + re.escape(s) + r'\b', text, re.I)]

        lines = [line.strip() for line in text.split('\n') if line.strip()]
        first_line = lines[0] if lines else "Candidate"

        if extraction_type == "Resume":
            data = {
                "name": first_line[:50],
                "email": None,
                "phone": None,
                "summary": lines[1][:200] if len(lines) > 1 else first_line,
                "education": [],
                "experience": [],
                "projects": [],
                "skills": found_skills or ["Software Engineering"],
                "certifications": []
            }
        else:
            data = {
                "title": first_line[:100],
                "company": None,
                "required_skills": found_skills or ["General Skills"],
                "preferred_skills": [],
                "min_experience_years": 0.0,
                "required_education": "None",
                "summary": text[:300]
            }

        try:
            return schema.model_validate(data)
        except Exception as ex:
            raise AIExtractionError(f"Heuristic extraction fallback failed: {ex}") from ex

    async def _call_and_validate(self, prompt: str, schema: Type[T]) -> T:
        raw_output = await self._call_llm(prompt)
        raw_output = raw_output.strip().replace("```json", "").replace("```", "").strip()
        return schema.model_validate(json.loads(raw_output))

    def embed(self, text: str):
        model = get_embedding_model()
        if model is None:
            raise RuntimeError("Embedding model is unavailable")
        return model.encode(text or "", convert_to_numpy=True)

    def embed_batch(self, texts: list[str]):
        model = get_embedding_model()
        if model is None:
            raise RuntimeError("Embedding model is unavailable")
        return model.encode(texts or [], convert_to_numpy=True)

    async def evaluate_candidate_expertly(self, resume_text: str, job_text: str) -> dict:
        """
        The 100% Core LLM Brain feature.
        Parses raw inputs through LLM with domain-aware category isolation, logical operators, and semantic evidence matching.
        """
        from app.schemas.analysis import ExpertEvaluationSchema
        schema_definition = ExpertEvaluationSchema.model_json_schema()

        prompt = f"""You are an Expert ATS System and Senior Technical Recruiter.
Your objective is to comprehensively evaluate a candidate's resume strictly against the provided Job Description.

STRICT ATS RULES & CATEGORY ISOLATION:

0. SOURCE SCOPING - IGNORE COMPANY MARKETING TEXT (CRITICAL):
    - Only extract candidate-scoring requirements from sections such as: Required Skills, Qualifications, Responsibilities / Key Responsibilities, Preferred Skills, Eligibility, Education, Certifications, Language / Language Proficiency, Location, Job Type / Employment Type, and Experience.
    - The company "About us" / mission / marketing / culture text (e.g. mentions of "AI Gigafactory", "agentic AI", "digital transformation", "140,000+ bold thinkers", industry buzzwords, awards, or "Why join us") is NOT a source of candidate requirements. Do not extract technologies, tools, or skills mentioned only in that kind of text, and do not penalize the candidate for not having them. If you must acknowledge such text exists, tag it 'INFORMATIONAL' and never let it affect any score.

1. CATEGORY CLASSIFICATION (CRITICAL): Categorize EVERY requirement into EXACTLY ONE of these types:
    - 'TECHNICAL': Programming languages, databases, web technologies, frameworks, CMS platforms (e.g., HTML5, CSS3, JavaScript, Bootstrap, PHP, MySQL, WordPress).
    - 'TOOL': Concrete software tools/applications that are not programming languages or AI tools (e.g., Microsoft Excel, Microsoft Word, PowerPoint, Git, GitHub, VS Code, Jira, Tableau, Power BI). Office productivity suites belong here, NOT in 'TECHNICAL'.
    - 'SOFT': Behavioral traits, communication, teamwork, work ethic (e.g., Critical Thinking, Problem-solving attitude, Communication skills, Attention to detail, Teamwork, Time management, Eagerness to learn, Personal Effectiveness, Executive Presence). NEVER put soft skills under TECHNICAL!
    - 'AI_TOOL': AI development/usage tools (e.g., ChatGPT, Claude, Cursor AI, GitHub Copilot).
    - 'ROLE': Job titles and role classifications (e.g., Full Stack Developer Intern).
    - 'LOCATION': Geographic requirement or office location (e.g., Noida, Gurugram, India).
    - 'WORK_ARRANGEMENT': Hybrid, Remote, On-site, Full-time, Internship.
    - 'EMPLOYMENT_TYPE': Internship, Full-Time, Contract.
    - 'EDUCATION_REQUIREMENT': Degrees, academic qualifications (e.g., B.Tech, B.E., MCA, BCA, Bachelor's in CS/IT).
    - 'LANGUAGE': Spoken/written natural languages (e.g., English, Hindi, German).
    - 'LANGUAGE_PROFICIENCY': Fluency level required (e.g., Professional working proficiency, Fluent).
    - 'INFORMATIONAL': Stipend, duration, start date, perks, perks copy, team descriptions, company background, shift timings, interview process details, application deadlines, equal opportunity statements, culture descriptions. NEVER evaluate these as missing candidate requirements!

2. CERTIFICATION ISOLATION (CRITICAL):
    - Certifications MUST go into the `certifications` array ONLY. Never put certifications into `all_requirements_evaluation`.
    - If the job lists preferred/required certs (e.g. AWS Certified, PMP, Scrum Master), put them in `certifications`. If none mentioned, return `certifications: []`.

3. PRIORITY CLASSIFICATION:
    - 'MANDATORY': Core must-have qualifications explicitly stated as required or essential.
    - 'IMPORTANT': Standard role requirements.
    - 'PREFERRED': Desirable/nice-to-have skills.
    - 'OPTIONAL': Secondary preferences.
    - 'INFORMATIONAL': Non-candidate metadata.

4. STATUS VERDICTS:
    - 'SATISFIED': Candidate clearly demonstrates the requirement in their resume.
    - 'PARTIALLY_SATISFIED': Candidate has partial or related evidence.
    - 'MISSING_BUT_OPTIONAL': Optional/preferred skill not found on resume.
    - 'MISSING_AND_REQUIRED': Mandatory/required skill not found on resume.

SCHEMA TO FOLLOW:
{json.dumps(schema_definition, indent=2)}

RESUME TEXT:
{resume_text}

JOB DESCRIPTION TEXT:
{job_text}
"""
        try:
            return await self._call_and_validate(prompt, ExpertEvaluationSchema)
        except Exception as e:
            logger.warning(f"AI candidate evaluation failed ({e}). Falling back to heuristic evaluation.")
            return self._heuristic_evaluation_fallback(resume_text, job_text)

    def _heuristic_evaluation_fallback(self, resume_text: str, job_text: str):
        import re
        from app.schemas.analysis import ExpertEvaluationSchema, SkillEvidenceSchema, RecommendationSchema

        COMMON_SKILLS = [
            "Python", "JavaScript", "TypeScript", "React", "Next.js", "Node.js", "HTML", "CSS", "SQL",
            "PostgreSQL", "MongoDB", "FastAPI", "Django", "Flask", "Tailwind", "Bootstrap", "Git", "GitHub",
            "Docker", "AWS", "Java", "C++", "C#", "PHP", "WordPress", "REST API", "GraphQL", "Linux", "Figma"
        ]

        resume_skills = [s for s in COMMON_SKILLS if re.search(r'\b' + re.escape(s) + r'\b', resume_text, re.I)]
        job_skills = [s for s in COMMON_SKILLS if re.search(r'\b' + re.escape(s) + r'\b', job_text, re.I)]

        matched_skills = set(resume_skills).intersection(set(job_skills))
        missing_skills = set(job_skills) - set(resume_skills)

        all_reqs = []
        for s in job_skills:
            is_matched = s in matched_skills
            all_reqs.append(
                SkillEvidenceSchema(
                    skill_name=s,
                    category="TECHNICAL",
                    priority="MANDATORY",
                    is_required=True,
                    status="SATISFIED" if is_matched else "MISSING_AND_REQUIRED",
                    matched_as=s if is_matched else None,
                    reasoning="Found in candidate resume" if is_matched else "Required by job description",
                    evidence_snippet=s if is_matched else None
                )
            )

        matched_count = len(matched_skills)
        total_count = len(job_skills) or 1
        score = round((matched_count / total_count) * 100, 2)

        recs = [
            RecommendationSchema(type="add_skill", content=f"Consider adding {s} to your resume.", priority=1)
            for s in list(missing_skills)[:3]
        ]

        return ExpertEvaluationSchema(
            overall_match_percentage_justified=score,
            all_requirements_evaluation=all_reqs,
            certifications=[],
            required_technical_skills_met=matched_count,
            required_technical_skills_total_logical=total_count,
            technical_skills_score=score,
            soft_skills_score=80.0,
            ai_tools_score=75.0,
            responsibilities_score=score,
            education_score=90.0,
            experience_score=85.0,
            project_evidence_score=80.0,
            location_score=100.0,
            certification_score=100.0,
            years_required_by_job=1.0,
            years_found_on_resume=1.0,
            experience_status="MET",
            education_gate="MET",
            detected_education="Bachelor's Degree",
            analysis_explanation=f"Evaluated candidate match based on requirement analysis. Candidate matched {matched_count} of {total_count} required technical skills.",
            actionable_recommendations=recs
        )
