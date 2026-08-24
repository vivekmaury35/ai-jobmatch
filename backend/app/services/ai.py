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
        provider = (settings.AI_PROVIDER or "gemini").lower()
        if provider == "groq" and not settings.GROQ_API_KEY:
            provider = "gemini"
        if provider == "openrouter" and not settings.OPENROUTER_API_KEY:
            provider = "gemini"

        self.provider = provider

        if self.provider == "openrouter":
            self.client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.OPENROUTER_API_KEY)
            self.model = settings.OPENROUTER_MODEL
        elif self.provider == "groq":
            self.client = AsyncOpenAI(base_url="https://api.groq.com/openai/v1", api_key=settings.GROQ_API_KEY)
            self.model = settings.GROQ_MODEL
        else:
            gemini_key = settings.GEMINI_API_KEY or os.getenv("GEMINI_API_KEY", "")
            self.client = genai.Client(api_key=gemini_key)
            self.model = "gemini-3.6-flash"


    async def _call_llm(self, prompt: str):
        if self.provider in ["openrouter", "groq"]:
            @retry(retry=retry_if_exception_type(Exception), stop=stop_after_attempt(3), wait=wait_exponential(multiplier=2, min=3, max=10))
            async def _call():
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    response_format={"type": "json_object"}
                )
                return response.choices[0].message.content
            return await _call()
        else:
            @retry(retry=retry_if_exception_type(Exception), stop=stop_after_attempt(5), wait=wait_exponential(multiplier=3, min=6, max=25))
            async def _call():
                return await self.client.aio.models.generate_content(model=self.model, contents=prompt)
            response = await _call()
            return response.text.strip()


    async def extract_structured(self, text: str, schema: Type[T], extraction_type: str) -> T:
        schema_definition = schema.model_json_schema()

        # Hardened system instructions for structured extraction
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
            logger.exception("Extraction failed")
            raise AIExtractionError("Failed to extract data.") from e

    async def _call_and_validate(self, prompt: str, schema: Type[T]) -> T:
        raw_output = await self._call_llm(prompt)
        raw_output = raw_output.strip().replace("```json", "").replace("```", "").strip()
        return schema.model_validate(json.loads(raw_output))

    def embed(self, text: str): return get_embedding_model().encode(text or "", convert_to_numpy=True)
    def embed_batch(self, texts: list[str]): return get_embedding_model().encode(texts or [], convert_to_numpy=True)

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
    - 'LOCATION': City, state, region, or country (e.g., Noida, India).
    - 'WORK_ARRANGEMENT': Work location mode (e.g., In-person, Remote, Hybrid).
    - 'ELIGIBILITY': Career stage/status requirements (e.g., Freshers, Final-year students, currently pursuing a degree).
    - 'EDUCATION_REQUIREMENT': Degree/field requirements (e.g., "Bachelor's degree in business, finance, computer science, engineering, or a related field", "Bachelor's Degree").
    - 'RESPONSIBILITY': Core duties, deliverables, domain skills like market research or reporting (e.g., "Conduct market research and analyze trends", "Prepare reports and presentations", "Support project management activities").
    - 'LANGUAGE': A spoken/written language requirement (e.g., "English").
    - 'LANGUAGE_PROFICIENCY': A proficiency level tied to a language (e.g., "Intermediate - B1").
    - 'EMPLOYMENT_TYPE': The nature of the position (e.g., "Intern", "Fixed Term", "Full-time", "Contract").
    - 'INFORMATIONAL': Non-candidate job metadata such as stipend, duration, company description, benefits, web links, or "what we offer" content. INFORMATIONAL items MUST NEVER be marked as missing candidate requirements or lower any score!
    - NOTE: Certifications (e.g., "Google Data Analytics", "Microsoft Certified: Power BI Data Analyst Associate", "Tableau Desktop Specialist") must NEVER go into `all_requirements_evaluation` at all - see rule 8 (CERTIFICATIONS) below, they belong exclusively in the separate `certifications` array.

2. REQUIREMENT PRIORITY (CRITICAL - drives scoring impact): Every item in `all_requirements_evaluation` must set a `priority`:
    - 'MANDATORY': Explicitly listed under "Required Skills", "Requirements", "Must have", or phrased as a hard requirement (e.g. "must", "required").
    - 'IMPORTANT': Listed under general "Qualifications" / core Responsibilities without softening language, or a core Education/Eligibility gate.
    - 'PREFERRED': Listed under "Preferred Skills", "Good to have", "Nice to have", "Bonus", or similar softened language.
    - 'OPTIONAL': Minor/illustrative extras, secondary tools mentioned only as examples.
    - 'INFORMATIONAL': Company description / marketing / benefits content that should never affect scoring (also always use category 'INFORMATIONAL' for these).
    A missed PREFERRED or OPTIONAL requirement must NEVER be treated as harshly as a missed MANDATORY one - scoring downstream applies priority-based weighting automatically, so your job is simply to classify priority accurately and honestly based on the JD's own language.

3. COMPOUND REQUIREMENT DECOMPOSITION (CRITICAL): Many requirements bundle multiple atomic skills using parentheses, commas, slashes, "and", or "or". You MUST decompose these and populate `atomic_components` (the individual atomic skill names) and `logical_operator` ("AND" if the candidate should ideally have all components, "OR" if any single alternative satisfies the requirement):
    - "Microsoft Office Suite (Word, Excel, PowerPoint)" -> skill_name="Microsoft Office Suite", atomic_components=["Microsoft Word","Microsoft Excel","Microsoft PowerPoint"], logical_operator="AND", category='TOOL'.
    - "HTML, CSS, and JavaScript" -> these are three separate AND requirements (you may emit them as one entry with atomic_components=["HTML","CSS","JavaScript"], logical_operator="AND", or as three separate entries - either is acceptable as long as each atom is evaluated).
    - "MySQL/PostgreSQL" or "MySQL or PostgreSQL" -> atomic_components=["MySQL","PostgreSQL"], logical_operator="OR". The candidate does NOT need both; either one fully satisfies the requirement.
    - "Django / Flask / FastAPI" -> atomic_components=["Django","Flask","FastAPI"], logical_operator="OR" (alternative framework options), UNLESS the JD text explicitly says all are required.
    - "Git/GitHub" -> atomic_components=["Git","GitHub"], logical_operator="OR".
    - "Node.js or Laravel/PHP" -> atomic_components=["Node.js","Laravel","PHP"], logical_operator="OR".
    For an AND group, if only SOME atomic components have resume evidence, set status='PARTIALLY_SATISFIED' (never MISSING) and list exactly which components matched in `matched_resume_evidence` and which didn't in your reasoning. Do NOT mark a whole compound requirement as missing just because the umbrella phrase itself ("Microsoft Office Suite") doesn't appear verbatim in the resume - what matters is whether its atomic components are present.

4. NORMALIZATION / ALIAS AWARENESS (do not require exact text matching): Treat these as equivalent when comparing JD requirements to resume content (this list is illustrative, not exhaustive - apply the same reasoning to any similar variant):
    "MS Excel" = "Microsoft Excel" = "Excel"; "MS Word" = "Microsoft Word" = "Word"; "PowerPoint" = "MS PowerPoint" = "Microsoft PowerPoint";
    "Node" = "NodeJS" = "Node.js"; "React JS" = "ReactJS" = "React.js" = "React"; "Next JS" = "NextJS" = "Next.js";
    "REST API" = "REST APIs" = "RESTful API(s)"; "Postgres" = "PostgreSQL"; "JS" = "JavaScript"; "TS" = "TypeScript"; "GitHub" = "Git Hub".
    Also ignore case, punctuation, and plural/singular differences (e.g. "database" = "databases", "API" = "APIs").

5. LOGICAL OPERATORS & DEGREE EQUIVALENCE ('ANY_OF'):
    - When a JD lists "B.Tech / BCA / MCA" or "business, finance, computer science, engineering, or a related field", interpret '/' and 'or' as logical OR across alternatives.
    - Map common degree abbreviations to their broad field before comparing: BCA/B.Sc Computer Science/MCA -> "computer science"; B.Tech/B.E./M.Tech -> "engineering"; BBA/MBA -> "business"; B.Com/M.Com -> "finance/commerce". Example: "Bachelor of Computer Applications" satisfies a requirement for "computer science, engineering, business, or finance" via the computer-science mapping - mark EDUCATION_REQUIREMENT as SATISFIED, not missing.
    - Status matching: "BCA Final Year", "pursuing BCA", or "fresher" satisfies "freshers or final-year students" (category ELIGIBILITY).

6. ILLUSTRATIVE EXAMPLES & "LIKE" / "SUCH AS" LANGUAGE:
    - Phrases like "Use AI tools like ChatGPT, Claude, Cursor AI, or GitHub Copilot" indicate illustrative examples under AI-assisted development. If the candidate has experience with AT LEAST ONE AI tool (e.g., GitHub Copilot or ChatGPT), the requirement is SATISFIED.

7. EVIDENCE-BASED SOFT SKILL & RESPONSIBILITY MATCHING (CRITICAL - do not hallucinate):
    - NEVER mark a soft skill or responsibility as SATISFIED just because the resume "sounds generically impressive". You must find and quote genuine, specific evidence from the resume text into `evidence_snippet` (a real substring/paraphrase of an actual resume sentence or bullet) AND into `matched_resume_evidence` (list containing that same evidence). If no real, specific evidence exists, mark it MISSING_BUT_OPTIONAL (priority PREFERRED/OPTIONAL) or MISSING_AND_REQUIRED (priority MANDATORY/IMPORTANT) - never invent evidence.
    - Semantic equivalence is fine for responsibilities/soft skills - exact wording is NOT required. Examples:
      * JD "Prepare reports and presentations" ~ Resume "Created analytical reports and presented insights" -> SATISFIED (paraphrase, same meaning).
      * JD "Conduct market research and analyze trends" ~ Resume "Performed research and analyzed data trends" -> SATISFIED (strong semantic match).
      * "Collaborated with a team of developers" -> evidence for "Teamwork"/"Collaboration".
      * "Analyzed datasets and identified trends" -> evidence for "Analytical Thinking"/"Research Analysis".
      * "Presented findings to stakeholders" -> evidence for "Communication"/"Storytelling"/"Presentation".
      * "Managed multiple deadlines" -> evidence for "Time Management".
    - Search the ENTIRE resume (Summary, Experience, Projects, Achievements, Education, Skills) for such evidence before concluding a requirement is missing.

8. CERTIFICATIONS - HANDLE SEPARATELY FROM TECHNICAL SKILLS (CRITICAL): Any certification named in the JD (e.g., "Google Data Analytics - Coursera", "Microsoft Certified: Power BI Data Analyst Associate", "Tableau Desktop Specialist") must be reported ONLY in the top-level `certifications` array, never in `all_requirements_evaluation`, and never counted as a missing technical skill.
    For each certification, set:
      * `priority`: 'REQUIRED' only if the JD explicitly says the certification is mandatory/required to apply; 'PREFERRED' if listed under a "Certifications" or "Preferred" heading without mandatory language (this is the common case); 'RECOMMENDED' if described as a nice bonus; 'INFORMATIONAL' if it's just contextual (e.g. certifications the *team* holds, not the candidate).
      * `matched`: true only if the resume genuinely lists that certification or a very close equivalent.
      * `matched_resume_evidence`: the resume text that proves it, or null.
      * `reasoning`: a short honest explanation.
    Certifications that are PREFERRED/RECOMMENDED/INFORMATIONAL and missing must NOT be treated as a significant gap - they carry low scoring weight by design.

9. BASIC PROFICIENCY THRESHOLDING:
    - Requirements for "basic knowledge", "WordPress basics", or "basic backend features" are satisfied by basic, working, intermediate, or advanced proficiency.

10. LOCATION & WORK MODE (CRITICAL - do not assume a match): Only mark LOCATION/WORK_ARRANGEMENT as SATISFIED when there is real resume evidence. Distinguish:
    - Exact city match, same-state match, same-country match, "Remote", "Hybrid", explicit "willing to relocate", vs. no location evidence at all in the resume (in which case mark MISSING_BUT_OPTIONAL unless the JD requires a specific location, in which case MISSING_AND_REQUIRED). Never default to SATISFIED just because the JD didn't emphasize location strongly.

11. SUB-SCORES COMPUTATION (0.0 to 100.0, or null):
    - Compute genuine, accurate sub-scores:
      * technical_skills_score: percentage of required TECHNICAL + TOOL requirements met (counting atomic components for compound requirements, e.g. 9/9 = 100.0).
      * soft_skills_score: percentage of soft skills satisfied by real evidence.
      * ai_tools_score: percentage of AI tool requirements met. Return null if no AI tools are mentioned in the JD.
      * responsibilities_score: percentage of key responsibilities met (semantic evidence counts).
      * education_score: 100.0 if the education/eligibility gate is met (including via degree-field mapping).
      * experience_score: 100.0 for freshers when the position explicitly targets freshers/interns.
      * project_evidence_score: 100.0 if project experience aligns with the role.
      * location_score: 100.0 if location & work arrangement are matched with real evidence. Return null if the JD does not specify location.
      * certification_score: percentage of REQUIRED-priority certifications met. Return null (not 0.0) if the JD lists no REQUIRED certifications - missing PREFERRED/RECOMMENDED certifications should NOT reduce this score.
      * overall_match_percentage_justified: Weighted overall score reflecting actual evidence strength and requirement priority (a missed PREFERRED item should barely move this number; a missed MANDATORY item should move it significantly).
    - IMPORTANT: Return null (not 0.0) for any sub-score category that does NOT appear in the job description. Only return 0.0 when the JD explicitly requires something and the candidate has zero evidence for it.

Output strictly valid JSON exactly conforming to this schema:
{json.dumps(schema_definition, indent=2)}

--- TARGET JOB DESCRIPTION ---
{job_text}

--- CANDIDATE RESUME ---
{resume_text}
"""
        return await self._call_and_validate(prompt, ExpertEvaluationSchema)

    async def generate_explanation(self, context: dict) -> dict:
        prompt = f"Analyze candidate match context and return JSON with 'explanation' string and 'recommendations' list: {json.dumps(context)}"
        raw_output = await self._call_llm(prompt)
        raw_output = raw_output.strip().replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(raw_output)
        except Exception as e:
            raise AIExtractionError("Failed to parse explanation JSON") from e
