"""Application settings.

This module centralizes all environment variables so the rest of the codebase
reads configuration from a single place.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed application configuration loaded from environment variables."""

    app_env: str = Field(default="dev", alias="APP_ENV")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    openai_chat_model: str = Field(default="gpt-4.1-mini", alias="OPENAI_CHAT_MODEL")
    openai_embedding_model: str = Field(
        default="text-embedding-3-small",
        alias="OPENAI_EMBEDDING_MODEL",
    )

    qdrant_path: str = Field(default="./data/qdrant", alias="QDRANT_PATH")
    qdrant_collection: str = Field(default="site_kb", alias="QDRANT_COLLECTION")

    brave_search_api_key: str = Field(default="", alias="BRAVE_SEARCH_API_KEY")
    pixabay_api_key: str = Field(default="", alias="PIXABAY_API_KEY")

    leads_file: str = Field(default="./data/leads.jsonl", alias="LEADS_FILE")
    allowed_origins: str = Field(
        default="http://localhost:3000,http://127.0.0.1:3000",
        alias="ALLOWED_ORIGINS",
    )

    max_web_results: int = Field(default=5, alias="MAX_WEB_RESULTS")
    max_image_results: int = Field(default=5, alias="MAX_IMAGE_RESULTS")
    kb_min_score: float = Field(default=0.55, alias="KB_MIN_SCORE")

    # Pydantic Settings loads from .env automatically.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def allowed_origins_list(self) -> list[str]:
        """Return CORS origins as a clean list."""
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]

    @property
    def leads_path(self) -> Path:
        """Convenience property for lead storage path."""
        return Path(self.leads_file)

    @property
    def qdrant_dir(self) -> Path:
        """Convenience property for local Qdrant directory."""
        return Path(self.qdrant_path)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cache settings for the whole process.

    FastAPI recommends using a cached dependency for settings because it avoids
    reading the .env file for every request.
    """
    return Settings()
