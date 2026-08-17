import json
import logging
from typing import Type, TypeVar

from google import genai
from pydantic import BaseModel, ValidationError
from sentence_transformers import SentenceTransformer

from app.core.config import settings


logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class AIExtractionError(Exception):
    pass


class AIService:
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise AIExtractionError(
                "Gemini API key is not configured."
            )

        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY
        )

        # Gemini structured extraction model
        self.model = "gemini-3.6-flash"

        # Local embedding model
        self.embedding_model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    async def extract_structured(
        self,
        text: str,
        schema: Type[T],
        extraction_type: str
    ) -> T:
        """
        Extract structured data from a document using Gemini.
        """

        schema_definition = schema.model_json_schema()

        base_prompt = f"""
You are an expert AI parser extracting structured data from a
{extraction_type}.

Read the document carefully.

OUTPUT REQUIREMENTS:
- Return ONLY valid JSON.
- Do not return markdown.
- Do not use ```json.
- Do not add explanations or commentary.
- The JSON MUST strictly follow the schema below.

SCHEMA:
{json.dumps(schema_definition, indent=2)}

DOCUMENT TEXT:
{text}
"""

        try:
            return await self._call_and_validate(
                base_prompt,
                schema
            )

        except ValidationError as e:
            logger.warning(
                "Attempt 1 LLM extraction failed schema validation. "
                "Retrying. Errors: %s",
                e
            )

            retry_prompt = f"""
{base_prompt}

YOUR PREVIOUS RESPONSE FAILED PYDANTIC SCHEMA VALIDATION.

VALIDATION ERRORS:
{str(e)}

Return ONLY a corrected valid JSON object.
Do not return markdown.
Do not add explanations.
"""

            try:
                return await self._call_and_validate(
                    retry_prompt,
                    schema
                )

            except Exception as retry_e:
                logger.exception(
                    "Attempt 2 LLM extraction failed."
                )

                raise AIExtractionError(
                    "Failed to extract valid structured data "
                    "from the document."
                ) from retry_e

        except Exception as api_e:
            logger.exception(
                "Gemini API request failed: %s",
                api_e
            )

            raise AIExtractionError(
                "AI Provider failed to process the request."
            ) from api_e

    async def _call_and_validate(
        self,
        prompt: str,
        schema: Type[T]
    ) -> T:

        response = await self.client.aio.models.generate_content(
            model=self.model,
            contents=prompt,
        )

        raw_output = response.text.strip()

        # Remove markdown fences if Gemini returns them.
        if raw_output.startswith("```json"):
            raw_output = raw_output[len("```json"):]

        elif raw_output.startswith("```"):
            raw_output = raw_output[len("```"):]

        if raw_output.endswith("```"):
            raw_output = raw_output[:-3]

        raw_output = raw_output.strip()

        parsed_dict = json.loads(raw_output)

        return schema.model_validate(parsed_dict)

    # ==========================================================
    # LOCAL EMBEDDINGS
    # ==========================================================

    def embed(self, text: str):
        """
        Generate a single embedding vector using
        sentence-transformers.
        """

        if not text:
            return self.embedding_model.encode(
                "",
                convert_to_numpy=True
            )

        return self.embedding_model.encode(
            text,
            convert_to_numpy=True
        )

    def embed_batch(self, texts: list[str]):
        """
        Generate embeddings for multiple strings.
        """

        if not texts:
            return []

        return self.embedding_model.encode(
            texts,
            convert_to_numpy=True
        )

    async def generate_explanation(
        self,
        context: dict
    ) -> str:
        """
        Stub for later explanation-generation phase.
        """

        raise NotImplementedError(
            "Explanation generation is not implemented yet."
        )