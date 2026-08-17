import json
import logging
from typing import Type, TypeVar
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from openai import AsyncOpenAI
from google import genai
from google.genai.errors import APIError
from pydantic import BaseModel, ValidationError
from sentence_transformers import SentenceTransformer
from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class AIExtractionError(Exception):
    pass

class AIService:
    def __init__(self):
        self.provider = settings.AI_PROVIDER
        if self.provider == "openrouter":
            self.client = AsyncOpenAI(base_url="https://openrouter.ai/api/v1", api_key=settings.OPENROUTER_API_KEY)
            self.model = settings.OPENROUTER_MODEL
        else:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.model = "gemini-3.6-flash"
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

    async def _call_llm(self, prompt: str):
        if self.provider == "openrouter":
            response = await self.client.chat.completions.create(model=self.model, messages=[{"role": "user", "content": prompt}], response_format={"type": "json_object"})
            return response.choices[0].message.content
        else:
            @retry(retry=retry_if_exception_type(APIError), stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
            async def _call(): return await self.client.aio.models.generate_content(model=self.model, contents=prompt)
            response = await _call()
            return response.text.strip()

    async def extract_structured(self, text: str, schema: Type[T], extraction_type: str) -> T:
        schema_definition = schema.model_json_schema()
        base_prompt = f"Extract structured data from {extraction_type}.\nSCHEMA:\n{json.dumps(schema_definition)}\n\nTEXT:\n{text}"
        try:
            return await self._call_and_validate(base_prompt, schema)
        except Exception as e:
            logger.exception("Extraction failed")
            raise AIExtractionError("Failed to extract data.") from e

    async def _call_and_validate(self, prompt: str, schema: Type[T]) -> T:
        raw_output = await self._call_llm(prompt)
        raw_output = raw_output.strip().replace("```json", "").replace("```", "").strip()
        return schema.model_validate(json.loads(raw_output))

    def embed(self, text: str): return self.embedding_model.encode(text or "", convert_to_numpy=True)
    def embed_batch(self, texts: list[str]): return self.embedding_model.encode(texts or [], convert_to_numpy=True)

    async def generate_explanation(self, context: dict) -> dict:
        json_example = json.dumps({"explanation": "...", "recommendations": [{"type": "add_skill", "content": "Improve skill X", "priority": 1}]})
        prompt = f"Analyze resume match: {json.dumps(context)}.\nReturn ONLY JSON as: {json_example}"
        try:
            raw = await self._call_llm(prompt)
            raw = raw.strip().replace("```json", "").replace("```", "").strip()
            parsed = json.loads(raw)
            return {"explanation": str(parsed.get("explanation", "")), "recommendations": parsed.get("recommendations", [])[:4]}
        except Exception as e:
            logger.exception("generate_explanation failed: %s", e)
            raise AIExtractionError("Failed to generate explanation.") from e
