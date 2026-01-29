"""Gemini AI integration service."""
from __future__ import annotations

import json
import time
from typing import Dict

from fastapi import HTTPException

from app.config import config

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None


class GeminiService:
    """Service for interacting with Google Gemini AI."""
    
    def __init__(self) -> None:
        self._client = None
    
    def _get_client(self):
        """Get or create Gemini client."""
        if not config.GOOGLE_API_KEY:
            raise HTTPException(
                status_code=500,
                detail="GOOGLE_API_KEY not configured"
            )
        
        if genai is None:
            raise HTTPException(
                status_code=500,
                detail="google-genai library not installed"
            )
        
        if self._client is None:
            self._client = genai.Client(api_key=config.GOOGLE_API_KEY)
        
        return self._client
    
    def parse_trading_condition(
        self,
        message: str,
        current_row: Dict[str, str]
    ) -> Dict[str, object]:
        """
        Parse natural language trading condition using Gemini AI.
        
        Args:
            message: User's natural language command
            current_row: Current CSV row data for context
            
        Returns:
            Dictionary with 'assistant_message' and 'spec' keys
            
        Raises:
            HTTPException: If API call fails or response is invalid
        """
        client = self._get_client()
        
        prompt = self._build_prompt(message, current_row)
        
        try:
            start_time = time.time()
            response = client.models.generate_content(
                model=config.GEMINI_MODEL,
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                ),
            )
            elapsed = time.time() - start_time
            
            # Parse JSON response
            try:
                data = json.loads(response.text)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=502,
                    detail="Invalid JSON response from Gemini AI"
                ) from exc
            
            # Validate response structure
            spec = data.get("spec", {})
            if not isinstance(spec, dict):
                raise HTTPException(
                    status_code=400,
                    detail="Gemini response missing valid spec"
                )
            
            return {
                "assistant_message": data.get("assistant_message", "Condition parsed successfully."),
                "spec": {
                    "field": str(spec.get("field", "")),
                    "operator": str(spec.get("operator", "")),
                    "value": str(spec.get("value", "")),
                    "value_type": str(spec.get("value_type", "string")),
                },
            }
            
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"Gemini AI error: {str(exc)}"
            ) from exc
    
    def _build_prompt(self, message: str, current_row: Dict[str, str]) -> str:
        """Build prompt for Gemini AI."""
        return (
            "You are a trading assistant. The user provides a natural language command. "
            "Use the provided CSV row to map fields accurately. "
            "Return JSON with: assistant_message (string), spec (object) where spec includes "
            "field (string), operator (one of ==, !=, >, >=, <, <=, contains, starts_with, ends_with), "
            "value (string), value_type (number|string). \n\n"
            f"User command: {message}\n\n"
            f"CSV row fields and values: {json.dumps(current_row, ensure_ascii=False)}\n\n"
            "Respond with JSON only."
        )


# Singleton instance
gemini_service = GeminiService()
