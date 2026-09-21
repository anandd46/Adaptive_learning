"""
Application configuration using pydantic-settings.
All settings are loaded from environment variables / .env file.
"""
from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration object. All values come from environment / .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Application ──────────────────────────────────────────
    app_env: Literal["development", "staging", "production"] = "development"
    app_name: str = "Adaptive Learning Platform"
    app_version: str = "1.0.0"
    debug: bool = True
    secret_key: str = "CHANGE_ME_generate_with_secrets_token_hex_32"

    # ─── Database ─────────────────────────────────────────────
    database_url: str = (
        "postgresql://alp_user:changeme@localhost:5432/adaptive_learning"
    )
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "adaptive_learning"
    postgres_user: str = "alp_user"
    postgres_password: str = "changeme"

    # ─── JWT Auth ─────────────────────────────────────────────
    jwt_secret_key: str = "CHANGE_ME_generate_with_secrets_token_hex_64"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # ─── LLM Provider ─────────────────────────────────────────
    llm_provider: Literal["google", "openai", "local"] = "google"
    google_api_key: str = ""
    google_model: str = "gemini-1.5-flash"
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.7
    llm_timeout_seconds: int = 30

    # ─── RAG & Vector Store ───────────────────────────────────
    vector_store: Literal["chromadb", "pgvector"] = "chromadb"
    chroma_persist_dir: str = "./rag/chroma_db"
    chroma_collection_prefix: str = "alp"
    embedding_model: str = "models/embedding-001"
    embedding_provider: str = "google"

    # ─── ML Pipeline ──────────────────────────────────────────
    model_store_dir: str = "./models"
    random_seed: int = 42
    ml_train_test_split: float = 0.2
    ml_validation_split: float = 0.1

    # ─── Rate Limiting ────────────────────────────────────────
    rate_limit_per_minute: int = 60
    llm_rate_limit_per_minute: int = 10

    # ─── CORS ─────────────────────────────────────────────────
    allowed_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    # ─── Logging ──────────────────────────────────────────────
    log_level: str = "INFO"
    log_format: Literal["json", "text"] = "json"

    # ─── Adaptive Engine ──────────────────────────────────────
    # Mastery thresholds
    mastery_beginner_threshold: float = 0.35
    mastery_intermediate_threshold: float = 0.65
    mastery_advanced_threshold: float = 0.85

    # Recommendation weights (must sum to 1.0)
    rec_weight_gap_score: float = 0.25
    rec_weight_mastery_deficit: float = 0.20
    rec_weight_accuracy_deficit: float = 0.20
    rec_weight_prereq_readiness: float = 0.15
    rec_weight_engagement: float = 0.10
    rec_weight_ml_confidence: float = 0.10

    @field_validator("rec_weight_gap_score")
    @classmethod
    def validate_weights(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("Weight must be between 0 and 1")
        return v

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings singleton."""
    return Settings()
