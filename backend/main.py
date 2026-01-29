"""
Stock Rotator Backend - Main Entry Point

Professional FastAPI application for real-time CSV data streaming
with AI-powered trading alerts using Google Gemini.

Directory Structure:
    app/
        ─ api/            # API routes and endpoints
         core/           # Configuration and utilities
         models/         # Pydantic models
         services/       # Business logic

To run:
    uvicorn main:app --reload --port 8000
    or
    uvicorn app.main:app --reload --port 8000
"""
from app.main import app

__all__ = ["app"]
