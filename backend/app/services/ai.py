import json
import logging
from typing import Type, TypeVar

from google import genai
from pydantic import BaseModel, ValidationError

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

        self.model_name = "gemini-3.6-flash"

    async def extract_structured(
        self,
        text: str,
        schema: Type[T],
        extraction_type: str
    ) -> T:

        schema_definition = schema.model_json_schema()

        base_prompt = f"""
You are an expert AI parser extracting structured data
from a {extraction_type}.

Read the document carefully.

OUTPUT REQUIREMENTS:
- Return ONLY valid JSON.
- Do not return markdown.
- Do not return ```json blocks.
- The JSON must follow this schema exactly.

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
                f"Attempt 1 validation failed. Retrying: {e}"
            )

            retry_prompt = f"""
{base_prompt}

Your previous response failed validation.

Validation errors:
{str(e)}

Return a corrected JSON object only.
"""

            try:
                return await self._call_and_validate(
                    retry_prompt,
                    schema
                )

            except Exception as retry_e:

                logger.error(
                    f"Attempt 2 failed: {retry_e}"
                )

                raise AIExtractionError(
                    "Failed to extract valid structured data."
                )

        except Exception as api_e:

            logger.error(
                f"Gemini API request failed: {api_e}"
            )

            raise AIExtractionError(
                "AI Provider failed to process the request."
            )

    async def _call_and_validate(
        self,
        prompt: str,
        schema: Type[T]
    ) -> T:

        response = await self.client.aio.models.generate_content(
            model=self.model_name,
            contents=prompt
        )

        raw_output = response.text.strip()

        if raw_output.startswith("```json"):
            raw_output = raw_output[7:]

        if raw_output.startswith("```"):
            raw_output = raw_output[3:]

        if raw_output.endswith("```"):
            raw_output = raw_output[:-3]

        raw_output = raw_output.strip()

        parsed_dict = json.loads(raw_output)

        return schema.model_validate(parsed_dict)

    async def generate_explanation(self, context: dict) -> str:
        pass

    def embed(self, text: str) -> list[float]:
        pass