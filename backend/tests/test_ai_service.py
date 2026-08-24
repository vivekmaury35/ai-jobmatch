import pytest
import json
from unittest.mock import AsyncMock, patch
from app.services.ai import AIService, AIExtractionError
from app.core.config import settings
from google.genai.errors import ServerError

@pytest.fixture
def ai_service(monkeypatch):
    monkeypatch.setattr(settings, "AI_PROVIDER", "gemini")
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "mock-key")
    with patch("google.genai.Client", return_value=AsyncMock()):
        return AIService()

@pytest.mark.anyio
async def test_generate_explanation_success(ai_service):
    mock_response = AsyncMock()
    mock_response.text = '{"explanation": "You are a great match.", "recommendations": [{"type": "add_skill", "content": "Learn X", "priority": 1}]}'

    with patch.object(ai_service.client.aio.models, 'generate_content', return_value=mock_response):
        context = {
            "overall_score": 50.0, "skill_score": 50.0,
            "experience_score": 50.0, "education_score": 50.0, "project_evidence_score": 50.0,
            "matched_skills": [], "missing_skills": [], "related_skills": []
        }
        result = await ai_service.generate_explanation(context)
        assert result["explanation"] == "You are a great match."
        assert len(result["recommendations"]) == 1

@pytest.mark.anyio
async def test_generate_explanation_retry_transient_error(ai_service):
    mock_response = AsyncMock()
    mock_response.text = '{"explanation": "Success after retries", "recommendations": []}'

    with patch.object(ai_service.client.aio.models, 'generate_content', side_effect=[ServerError(503, {}, None), ServerError(503, {}, None), mock_response]):
        context = {
            "overall_score": 50.0, "skill_score": 50.0,
            "experience_score": 50.0, "education_score": 50.0, "project_evidence_score": 50.0,
            "matched_skills": [], "missing_skills": [], "related_skills": []
        }
        result = await ai_service.generate_explanation(context)
        assert result["explanation"] == "Success after retries"

@pytest.mark.anyio
async def test_generate_explanation_malformed_json(ai_service):
    mock_response = AsyncMock()
    mock_response.text = '{"explanation": "no json close"'

    with patch.object(ai_service.client.aio.models, 'generate_content', return_value=mock_response):
        context = {
            "overall_score": 50.0, "skill_score": 50.0,
            "experience_score": 50.0, "education_score": 50.0, "project_evidence_score": 50.0,
            "matched_skills": [], "missing_skills": [], "related_skills": []
        }
        with pytest.raises(AIExtractionError):
            await ai_service.generate_explanation(context)
