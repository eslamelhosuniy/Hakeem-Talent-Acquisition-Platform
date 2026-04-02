import os
from functools import lru_cache
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


SRC_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = SRC_DIR.parent

class Settings(BaseSettings):

    APP_NAME: str = "AI Talent Platform"
    APP_VERSION: str = "0.1"

  
    FILE_ALLOWED_TYPES: list = ["application/pdf"]
    FILE_MAX_SIZE: int = 10  
    FILE_DEFAULT_CHUNK_SIZE: int = 512000


    DB_NAME: str = "database.db"
    
 
    DB_PATH: str = str(SRC_DIR / "database.db")
    DATABASE_URL: str = f"sqlite:///{DB_PATH}"


    POSTGRES_USERNAME: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_MAIN_DATABASE: str = "talent_db"

    GENERATION_BACKEND: str = "OPENAI"
    EMBEDDING_BACKEND: str = "OPENAI"
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_API_URL: Optional[str] = "https://api.openai.com/v1"
    USE_AI_EXPLANATION: bool = False

    INPUT_DAFAULT_MAX_CHARACTERS: int = 4096
    GENERATION_DAFAULT_MAX_TOKENS: int = 2000
    GENERATION_DAFAULT_TEMPERATURE: float = 0.1

    GENERATION_MODEL_ID: Optional[str] = "gpt-4o-mini"
    EMBEDDING_MODEL_ID: Optional[str] = "text-embedding-3-small"
    EMBEDDING_MODEL_SIZE: Optional[int] = 1536
    
  
    VECTOR_DB_BACKEND: str = "QDRANT"
    VECTOR_DB_PATH: str = str(SRC_DIR / "qdrant_db")
    VECTOR_DB_DISTANCE_METHOD: Optional[str] = "cosine"

  
    PRIMARY_LANG: str = "ar"
    DEFAULT_LANG: str = "en"

    model_config = SettingsConfigDict(
        env_file=(ROOT_DIR / ".env", SRC_DIR / ".env.example"),
        extra="ignore",
    )

@lru_cache()
def get_settings():
    return Settings()


settings = get_settings()