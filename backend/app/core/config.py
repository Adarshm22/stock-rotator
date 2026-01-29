"""Configuration settings for the application."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from backend/.env
ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(dotenv_path=ENV_PATH, override=False)


class Settings:
    """Application settings."""
    
    # Gemini AI
    GOOGLE_API_KEY: str = os.getenv("GOOGLE_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    
    # CORS
    ALLOWED_ORIGINS: str = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001")
    
    # CSV Data
    CSV_PATH: str | None = os.getenv("CSV_PATH")
    STATE_PATH: str = os.getenv("STATE_PATH", "backend_state.json")
    UPDATE_INTERVAL_SECONDS: int = 60
    
    # Default CSV paths
    DEFAULT_DATA_PATHS = [
        Path(__file__).resolve().parents[1] / "NIFTY_historical_data.csv",
        Path(__file__).resolve().parents[2] / "NIFTY_historical_data.csv",
    ]
    
    @property
    def cors_origins(self) -> list[str]:
        """Get list of allowed CORS origins."""
        origins = [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]
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


settings = Settings()
