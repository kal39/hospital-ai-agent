
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Hospital AI Assistant API"
    app_version: str = "0.1.0"
    environment: str = "development"

    port: int = 5000
    frontend_origin: str = "http://localhost:5173"

    # Demo authentication is only for synthetic local test patients.
    demo_auth_enabled: bool = True

    # Gemini configuration. Keep API keys in .env, never in source code.
    llm_api_key: str = ""
    llm_model: str = "gemini-flash-lite-latest"
    llm_fallback_model: str = "gemini-flash-latest"

    max_message_length: int = 2000
    rate_limit_window_ms: int = 60000
    rate_limit_max_requests: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
