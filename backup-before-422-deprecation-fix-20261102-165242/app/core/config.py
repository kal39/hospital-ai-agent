import ipaddress
import re
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

    # Comma-separated hostnames accepted by the backend.
    # Production must provide an explicit trusted-host allowlist.
    trusted_hosts: str = ""

    # Enable only for local development with synthetic patients.
    demo_auth_enabled: bool = True

    # Separate secret for local demo staff operations.
    demo_staff_token: str = ""

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

    @field_validator("trusted_hosts", mode="before")
    @classmethod
    def normalize_trusted_hosts(cls, value: object) -> str:
        if not isinstance(value, str):
            raise ValueError("TRUSTED_HOSTS must be a comma-separated string.")

        if not value.strip():
            return ""

        raw_hosts = value.split(",")
        hosts = [host.strip().lower() for host in raw_hosts]

        if not hosts or any(not host for host in hosts):
            raise ValueError(
                "TRUSTED_HOSTS cannot contain empty entries."
            )

        return ",".join(dict.fromkeys(hosts))

    @staticmethod
    def _validate_trusted_host(host: str) -> bool:
        candidate = host.rstrip(".")

        if not candidate or len(candidate) > 253:
            return False

        try:
            ipaddress.ip_address(candidate)
            return True
        except ValueError:
            pass

        labels = candidate.split(".")
        label_pattern = re.compile(
            r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
        )

        return all(
            len(label) <= 63 and label_pattern.fullmatch(label)
            for label in labels
        )

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

        trusted_hosts = [
            host.strip()
            for host in self.trusted_hosts.split(",")
            if host.strip()
        ]

        if not trusted_hosts:
            raise ValueError(
                "TRUSTED_HOSTS must be explicitly configured in production."
            )

        if any("*" in host for host in trusted_hosts):
            raise ValueError(
                "TRUSTED_HOSTS cannot contain wildcards in production."
            )

        for host in trusted_hosts:
            if not self._validate_trusted_host(host):
                raise ValueError(
                    "TRUSTED_HOSTS entries must be valid hostnames or IP addresses."
                )

            normalized_host = host.rstrip(".").lower()

            if normalized_host == "localhost" or normalized_host.endswith(".localhost"):
                raise ValueError(
                    "TRUSTED_HOSTS cannot contain localhost in production."
                )

            try:
                address = ipaddress.ip_address(normalized_host)
            except ValueError:
                address = None

            if address is not None and address.is_loopback:
                raise ValueError(
                    "TRUSTED_HOSTS cannot contain loopback IP addresses in production."
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
