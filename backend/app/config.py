"""Application configuration and environment management."""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from dotenv import load_dotenv

# Load environment variables
_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(dotenv_path=_ENV_PATH, override=False)


class Config:
    """Application configuration."""
    
    # Paths
    BASE_DIR = Path(__file__).resolve().parents[1]
    DATA_DIR = BASE_DIR
    
    # CSV Configuration
    CSV_PATH: Path | None = Path(os.getenv("CSV_PATH", "")).expanduser() if os.getenv("CSV_PATH") else None
    DEFAULT_CSV_PATHS: List[Path] = [
        BASE_DIR / "NIFTY_historical_data.csv",
        BASE_DIR.parent / "NIFTY_historical_data.csv",
    ]
    
    # State Management
    STATE_PATH: Path = Path(os.getenv("STATE_PATH", str(BASE_DIR / "backend_state.json"))).expanduser()
    
    # Update Settings
    UPDATE_INTERVAL_SECONDS: int = int(os.getenv("UPDATE_INTERVAL_SECONDS", "60"))
    
    # Gemini AI Configuration
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # CORS Configuration
    ALLOWED_ORIGINS: str = os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:3000,http://localhost:3001"
    )
    
    @classmethod
    def get_allowed_origins(cls) -> List[str]:
        """Get list of allowed CORS origins including development defaults."""
        origins = [origin.strip() for origin in cls.ALLOWED_ORIGINS.split(",") if origin.strip()]
        
        # Always include common dev origins
        dev_origins = [
            "http://localhost:3000",
            "https://localhost:3000",
            "http://127.0.0.1:3000",
            "https://127.0.0.1:3000",
        ]
        
        for origin in dev_origins:
            if origin not in origins:
                origins.append(origin)
        
        return origins


config = Config()
