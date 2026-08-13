import logging
import json
from PIL import Image
import google.generativeai as genai
from app.config import settings

logger = logging.getLogger("app.services.gemini_service")


class GeminiService:
    _configured = False

    @classmethod
    def _ensure_configured(cls):
        if not cls._configured:
            if settings.GEMINI_API_KEY:
                genai.configure(api_key=settings.GEMINI_API_KEY)
                cls._configured = True
                logger.info("Gemini API service configured successfully.")
            else:
                logger.warning("GEMINI_API_KEY is not set. Gemini fallback is unavailable.")

    @classmethod
    def analyze_image(cls, image_path: str) -> dict | None:
        """
        Sends the image to Gemini for OCR extraction and quality analysis.
        Returns a dictionary with keys:
            detected_number (str | None)
            is_blurry (bool)
            is_low_light (bool)
            confidence (float)
            issues (list[str])
        """
        cls._ensure_configured()
        if not cls._configured:
            return None

        try:
            # Load the image
            with Image.open(image_path) as img:
                # Initialize Gemini model
                model = genai.GenerativeModel("gemini-2.5-flash")
                
                # Define structured prompt
                prompt = (
                    "Analyze this image of a vehicle and return a JSON object with these exact keys:\n"
                    "{\n"
                    '  "detected_number": "the raw license plate text, or null if none found",\n'
                    '  "is_blurry": true/false,\n'
                    '  "is_low_light": true/false,\n'
                    '  "confidence": a float between 0.0 and 1.0 representing your confidence in the plate text (null if no plate),\n'
                    '  "issues": ["list of issues found, e.g., blurry, low light, partial view"]\n'
                    "}"
                )
                
                # Execute generation forcing JSON response format
                response = model.generate_content(
                    [prompt, img],
                    generation_config={"response_mime_type": "application/json"}
                )
                
                text_response = response.text.strip()
                result = json.loads(text_response)
                
                logger.info(f"Gemini fallback analysis completed successfully: {result}")
                return result
                
        except Exception as e:
            logger.error(f"Gemini fallback image analysis failed: {str(e)}")
            return None
