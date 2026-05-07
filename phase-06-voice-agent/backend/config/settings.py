"""Phase 06 settings — extends Phase 05 config with TTS vars."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    supabase_url: str
    supabase_service_role_key: str
    supabase_jwt_secret: str
    cors_origins: str = "http://localhost:5173"
    api_host: str = "0.0.0.0"
    api_port: int = 8002

    openrouter_api_key: str = ""
    openrouter_primary_model: str = "anthropic/claude-3.5-sonnet"
    openrouter_fallback_model: str = "google/gemini-2.0-flash"

    chroma_persist_dir: str = "./chroma_data"
    embedding_model: str = "BAAI/bge-large-en-v1.5"

    memory_update_interval: int = 5
    max_conversation_history: int = 10
    max_response_tokens: int = 512

    tts_default_voice: str = "en-IN-NeerjaNeural"
    tts_max_text_length: int = 1000
    voice_recording_timeout_s: int = 120


@lru_cache
def get_settings() -> Settings:
    return Settings()
