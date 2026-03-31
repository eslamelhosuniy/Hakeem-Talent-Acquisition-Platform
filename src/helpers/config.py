from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


SRC_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = SRC_DIR.parent


class Settings(BaseSettings):
    APP_NAME: str = "AI Talent Platform"
    APP_VERSION: str = "0.1"

    FILE_ALLOWED_TYPES: list = []
    FILE_MAX_SIZE: int = 10
    FILE_DEFAULT_CHUNK_SIZE: int = 512000

    POSTGRES_USERNAME: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_MAIN_DATABASE: str = "talent_db"

    GENERATION_BACKEND: str = "OPENAI"
    EMBEDDING_BACKEND: str = "OPENAI"

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_URL: Optional[str] = "https://api.openai.com/v1"
    USE_AI_EXPLANATION: bool = False

    GENERATION_MODEL_ID: Optional[str] = "gpt-4o-mini"
    EMBEDDING_MODEL_ID: Optional[str] = "text-embedding-3-small"
    EMBEDDING_MODEL_SIZE: Optional[int] = 1536
    INPUT_DAFAULT_MAX_CHARACTERS: Optional[int] = 4096
    GENERATION_DAFAULT_MAX_TOKENS: Optional[int] = 2000
    GENERATION_DAFAULT_TEMPERATURE: Optional[float] = 0.1

    VECTOR_DB_BACKEND: str = "QDRANT"
    VECTOR_DB_PATH: str = "qdrant_db"
    VECTOR_DB_DISTANCE_METHOD: Optional[str] = "cosine"

    PRIMARY_LANG: str = "en"
    DEFAULT_LANG: str = "en"

    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", SRC_DIR / ".env.example"),
        extra="ignore",
    )


@lru_cache()
def get_settings():
    return Settings()
