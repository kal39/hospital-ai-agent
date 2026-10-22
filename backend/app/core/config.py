from functools import lru_cache
from urllib.parse import urlsplit

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Hospital AI Assistant API"
    app_version: str = "0.1.0"
    environment: str = "development"

    port: int = 5000
    # No production origin is assumed. Configure FRONTEND_ORIGIN explicitly.
    frontend_origin: str = ""

    # Enable only for local development with synthetic patients.
    demo_auth_enabled: bool = True

    # Keep API keys in environment configuration, never in source code.
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

    @field_validator("environment", mode="before")
    @classmethod
    def validate_environment_name(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError(
                "ENVIRONMENT must be development, test, or production."
            )

        normalized = value.strip().lower()
        allowed = {"development", "test", "production"}

        if normalized not in allowed:
            raise ValueError(
                "ENVIRONMENT must be development, test, or production."
            )

        return normalized

    @model_validator(mode="after")
    def validate_rate_limit_settings(self) -> "Settings":
        if self.rate_limit_window_ms <= 0:
            raise ValueError(
                "RATE_LIMIT_WINDOW_MS must be greater than zero."
            )

        if self.rate_limit_max_requests <= 0:
            raise ValueError(
                "RATE_LIMIT_MAX_REQUESTS must be greater than zero."
            )

        return self

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.environment != "production":
            return self

        if self.demo_auth_enabled:
            raise ValueError(
                "DEMO_AUTH_ENABLED must be false in production."
            )

        origin = self.frontend_origin.strip().rstrip("/")
        if not origin:
            raise ValueError(
                "FRONTEND_ORIGIN must be configured in production."
            )

        try:
            parsed = urlsplit(origin)
            hostname = parsed.hostname
            # Accessing port also validates malformed port values.
            parsed.port
        except ValueError as exc:
            raise ValueError(
                "FRONTEND_ORIGIN must be a valid HTTPS origin."
            ) from exc

        if (
            parsed.scheme.lower() != "https"
            or not parsed.netloc
            or not hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError(
                "FRONTEND_ORIGIN must be an HTTPS origin without "
                "credentials, a path, a query, or a fragment."
            )

        normalized_host = hostname.lower()
        if (
            normalized_host == "localhost"
            or normalized_host.endswith(".localhost")
            or normalized_host in {"127.0.0.1", "::1"}
        ):
            raise ValueError(
                "FRONTEND_ORIGIN cannot point to localhost in production."
            )

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
