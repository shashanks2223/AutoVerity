import pytest
from unittest.mock import MagicMock, patch
from app.services.gemini_service import GeminiService
from app.config import settings


def test_gemini_service_disabled():
    """If GEMINI_API_KEY is not set, GeminiService should return None immediately."""
    settings.GEMINI_API_KEY = None
    GeminiService._configured = False
    res = GeminiService.analyze_image("some_path.jpg")
    assert res is None


@patch("google.generativeai.GenerativeModel")
@patch("google.generativeai.configure")
def test_gemini_service_success(mock_configure, mock_model_class):
    """If GEMINI_API_KEY is set, GeminiService should configure the SDK, call the API, and parse the JSON response."""
    settings.GEMINI_API_KEY = "test_gemini_key_123"
    GeminiService._configured = False

    # Create mock response object return value
    mock_response = MagicMock()
    mock_response.text = (
        '{\n'
        '  "detected_number": "DL3CA5678",\n'
        '  "is_blurry": false,\n'
        '  "is_low_light": true,\n'
        '  "confidence": 0.96,\n'
        '  "issues": ["Dim environment"]\n'
        '}'
    )

    mock_model_instance = MagicMock()
    mock_model_instance.generate_content.return_value = mock_response
    mock_model_class.return_value = mock_model_instance

    # Mock Image.open so we don't hit the filesystem
    with patch("PIL.Image.open") as mock_image_open:
        res = GeminiService.analyze_image("dummy.jpg")

        # Verify SDK configuration and model load
        mock_configure.assert_called_once_with(api_key="test_gemini_key_123")
        mock_model_class.assert_called_once_with("gemini-2.5-flash")

        # Verify parsing correctness
        assert res is not None
        assert res["detected_number"] == "DL3CA5678"
        assert res["is_blurry"] is False
        assert res["is_low_light"] is True
        assert res["confidence"] == 0.96
        assert "Dim environment" in res["issues"]
