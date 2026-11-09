import pytest
from pydantic import ValidationError

from app.core.config import Settings


def make_settings(**overrides):
    values = {
        "environment": "development",
        "demo_auth_enabled": True,
        "frontend_origin": "http://localhost:5173",
    }
    values.update(overrides)
    return Settings(_env_file=None, **values)


def test_development_allows_synthetic_demo_auth() -> None:
    settings = make_settings()
    assert settings.demo_auth_enabled is True


def test_production_accepts_explicit_https_origin_and_demo_auth_disabled() -> None:
    settings = make_settings(
        environment="production",
        demo_auth_enabled=False,
        frontend_origin="https://portal.example.org",
    )
    assert settings.environment == "production"
    assert settings.demo_auth_enabled is False


def test_production_rejects_enabled_demo_auth() -> None:
    with pytest.raises(ValidationError, match="DEMO_AUTH_ENABLED"):
        make_settings(
            environment="production",
            demo_auth_enabled=True,
            frontend_origin="https://portal.example.org",
        )


def test_production_rejects_missing_frontend_origin() -> None:
    with pytest.raises(ValidationError, match="FRONTEND_ORIGIN"):
        make_settings(
            environment="production",
            demo_auth_enabled=False,
            frontend_origin="",
        )


@pytest.mark.parametrize(
    "origin",
    [
        "http://portal.example.org",
        "http://localhost:5173",
        "https://localhost:5173",
        "https://127.0.0.1",
        "https://portal.example.org/app",
        "https://portal.example.org?debug=true",
    ],
)
def test_production_rejects_unsafe_frontend_origins(origin: str) -> None:
    with pytest.raises(ValidationError, match="FRONTEND_ORIGIN"):
        make_settings(
            environment="production",
            demo_auth_enabled=False,
            frontend_origin=origin,
        )

@pytest.mark.parametrize(
    ("setting", "value"),
    [
        ("rate_limit_window_ms", 0),
        ("rate_limit_window_ms", -1),
        ("rate_limit_max_requests", 0),
        ("rate_limit_max_requests", -1),
    ],
)
def test_rate_limit_settings_must_be_positive(setting, value):
    with pytest.raises(ValidationError):
        make_settings(**{setting: value})

@pytest.mark.parametrize(
    "environment",
    [
        "prodution",
        "staging",
        "",
        "local",
    ],
)
def test_unknown_environment_is_rejected(environment):
    with pytest.raises(ValidationError, match="ENVIRONMENT"):
        make_settings(environment=environment)


@pytest.mark.parametrize(
    ("environment", "expected"),
    [
        ("DEVELOPMENT", "development"),
        (" Production ", "production"),
        ("test", "test"),
    ],
)
def test_environment_names_are_normalized(environment, expected):
    settings = make_settings(
        environment=environment,
        demo_auth_enabled=False,
        frontend_origin="https://portal.example.org",
    )
    assert settings.environment == expected
