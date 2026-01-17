from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from typing import Optional
from pathlib import Path
import os


def find_env_file() -> Optional[str]:
    """Find .env file by searching current directory and parents."""
    current = Path.cwd()
    
    for path in [current, current.parent, current.parent.parent]:
        env_path = path / ".env"
        if env_path.exists():
            return str(env_path)
    return None


class Settings(BaseSettings):
    """
    Application configuration with validation.
    
    All settings can be configured via environment variables or .env file.
    Environment variables are case-insensitive.
    """
    
    google_api_key: str = ""
    youtube_api_key: str = ""
    
    database_url: str = "sqlite:///./youtube_cards.db"
    
    api_keys: str = ""
    allowed_origins: str = "http://localhost:5173"
    
    llm_model_name: str = "gemini-2.5-flash"
    llm_max_retries: int = 3
    llm_timeout: int = 60
    
    cache_ttl: int = 3600
    cache_max_size: int = 100
    
    log_level: str = "INFO"
    
    environment: str = "development"
    debug: bool = False
    testing: bool = False
    
    default_recipe_language: str = "English"
    
    usda_api_key: str = "DEMO_KEY"
    
    model_config = SettingsConfigDict(
        env_file=find_env_file(),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    @model_validator(mode='after')
    def validate_api_keys(self):
        """Validate required API keys are set unless in testing mode."""
        if not self.testing and self.environment != "testing":
            if not self.google_api_key:
                raise ValueError(
                    "GOOGLE_API_KEY is required. Set it in your .env file or as an environment variable."
                )
            if not self.youtube_api_key:
                raise ValueError(
                    "YOUTUBE_API_KEY is required. Set it in your .env file or as an environment variable."
                )
        return self
    
    @property
    def api_keys_list(self) -> list[str]:
        """Get API keys as a list."""
        if not self.api_keys:
            return []
        return [k.strip() for k in self.api_keys.split(",") if k.strip()]
    
    @property
    def allowed_origins_list(self) -> list[str]:
        """Get allowed origins as a list."""
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"


settings = Settings()

GOOGLE_API_KEY = settings.google_api_key
YOUTUBE_API_KEY = settings.youtube_api_key
DEFAULT_RECIPE_LANGUAGE = settings.default_recipe_language
SQLALCHEMY_DATABASE_URL = settings.database_url
