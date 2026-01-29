"""Gemini AI integration service."""
import json
import time
from fastapi import HTTPException

from google import genai
from google.genai import types

from app.core.config import settings


class GeminiService:
    """Service for interacting with Google Gemini AI."""
    
    def __init__(self):
        self._client = None
    
    def _get_client(self):
        """Get or create Gemini client."""
        if self._client is None:
            if not settings.GOOGLE_API_KEY:
                raise HTTPException(status_code=500, detail="GOOGLE_API_KEY is not set")
            self._client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        return self._client
    
    def parse_condition(self, message: str, row: dict[str, str]) -> dict[str, object]:
        """
        Parse natural language trading condition using Gemini AI.
        
        Args:
            message: User's natural language command
            row: Current CSV row data for context
            
        Returns:
            Dictionary with assistant_message and spec (field, operator, value, value_type)
        """
        try:
            client = self._get_client()
            prompt = (
                "You are a trading assistant. The user provides a natural language command. "
                "Use the provided CSV row to map fields accurately. "
                "Return JSON with: assistant_message (string), spec (object) where spec includes "
                "field (string), operator (one of ==, !=, >, >=, <, <=, contains, starts_with, ends_with), "
                "value (string), value_type (number|string). \n\n"
                f"User command: {message}\n\n"
                f"CSV row fields and values: {json.dumps(row, ensure_ascii=False)}\n\n"
                "Respond with JSON only."
            )

            print(f"[GEMINI] Sending request to {settings.GEMINI_MODEL}...")
            start_time = time.time()
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                ),
            )
            elapsed = time.time() - start_time
            print(f"[GEMINI] Response received in {elapsed:.2f}s")

            try:
                data = json.loads(response.text)
            except json.JSONDecodeError as exc:
                print(f"Gemini response parsing error: {exc}")
                print(f"Response text: {response.text}")
                raise HTTPException(status_code=502, detail="Invalid JSON from Gemini") from exc

            spec = data.get("spec", {})
            if not isinstance(spec, dict):
                raise HTTPException(status_code=400, detail="Gemini response missing spec")
            
            return {
                "assistant_message": data.get("assistant_message", "Condition parsed."),
                "spec": {
                    "field": str(spec.get("field", "")),
                    "operator": str(spec.get("operator", "")),
                    "value": str(spec.get("value", "")),
                    "value_type": str(spec.get("value_type", "string")),
                },
            }
        except Exception as exc:
            print(f"Error in parse_condition: {exc}")
            print(f"Exception type: {type(exc).__name__}")
            raise


# Global service instance
gemini_service = GeminiService()
