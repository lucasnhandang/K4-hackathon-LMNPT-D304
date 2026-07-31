"""Cấu hình toàn cục, đọc từ ``backend/.env``."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    mongo_uri: str = "mongodb://localhost:27017"
    mongo_db_name: str = "student_assistant"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    gemini_embedding_model: str = "gemini-embedding-2"
    embedding_dimensions: int = 768

    min_kb_similarity: float = 0.35
    min_confidence_to_answer: float = 0.6
    vector_search_index: str = "kb_vector_index"
    vector_answer_threshold: float = 0.83
    vector_clarify_threshold: float = 0.80
    vector_top_k: int = 5
    vector_num_candidates: int = 100

    max_message_characters: int = 2_000
    user_requests_per_minute: int = 5
    channel_requests_per_minute: int = 30
    raw_retention_days: int = 30
    redacted_retention_days: int = 180
    user_memory_retention_days: int = 180

    discord_bot_token: str = ""
    discord_allowed_channel_ids: str = ""
    discord_kb_channel_ids: str = "977644669326475311"
    knowledge_ingest_user_per_minute: int = 10
    knowledge_ingest_channel_per_minute: int = 60
    backend_base_url: str = "http://127.0.0.1:8000"
    backend_timeout_seconds: float = 90.0


settings = Settings()
