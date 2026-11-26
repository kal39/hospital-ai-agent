import pytest
from pydantic import ValidationError

from app.core.config import Settings


def make_settings(**overrides):
    values = {
        "environment": "development",
        "demo_auth_enabled": True,
        "frontend_origin": "http://localhost:5173",
        "trusted_hosts": "portal.example.org",
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



def test_production_requires_explicit_trusted_hosts() -> None:
    with pytest.raises(ValidationError, match="TRUSTED_HOSTS"):
        make_settings(
            environment="production",
            demo_auth_enabled=False,
            frontend_origin="https://portal.example.org",
            trusted_hosts="",
        )


def test_production_rejects_wildcard_trusted_hosts() -> None:
    with pytest.raises(ValidationError, match="wildcard"):
        make_settings(
            environment="production",
            demo_auth_enabled=False,
            frontend_origin="https://portal.example.org",
            trusted_hosts="*",
        )


def test_trusted_hosts_are_normalized_and_deduplicated() -> None:
    settings = make_settings(
        trusted_hosts=" portal.example.org, PORTAL.example.org, api.example.org "
    )
    assert settings.trusted_hosts == "portal.example.org,api.example.org"


def test_production_accepts_explicit_trusted_hosts() -> None:
    settings = make_settings(
        environment="production",
        demo_auth_enabled=False,
        frontend_origin="https://portal.example.org",
        trusted_hosts="portal.example.org,api.example.org",
    )
    assert settings.trusted_hosts == "portal.example.org,api.example.org"



def test_production_rejects_wildcard_subdomains() -> None:
    with pytest.raises(ValidationError, match="wildcards"):
        make_settings(
            environment="production",
            demo_auth_enabled=False,
            frontend_origin="https://portal.example.org",
            trusted_hosts="*.example.org",
        )



@pytest.mark.parametrize(
    "trusted_hosts",
    [
        "api.example.org/path",
        "api.example.org:5000",
        "https://api.example.org",
        "api..example.org",
        "-api.example.org",
        "api.example.org,",
    ],
)
def test_production_rejects_malformed_trusted_hosts(trusted_hosts):
    with pytest.raises(
        ValidationError,
        match="valid hostnames or IP addresses|empty entries",
    ):
        make_settings(
            environment="production",
            demo_auth_enabled=False,
            frontend_origin="https://portal.example.org",
            trusted_hosts=trusted_hosts,
        )


@pytest.mark.parametrize(
    "trusted_hosts",
    [
        "localhost",
        "api.localhost",
        "127.0.0.1",
        "::1",
    ],
)
def test_production_rejects_local_trusted_hosts(trusted_hosts):
    with pytest.raises(ValidationError):
        make_settings(
            environment="production",
            demo_auth_enabled=False,
            frontend_origin="https://portal.example.org",
            trusted_hosts=trusted_hosts,
        )


def test_production_accepts_valid_hostname_and_private_ip():
    settings = make_settings(
        environment="production",
        demo_auth_enabled=False,
        frontend_origin="https://portal.example.org",
        trusted_hosts="api.example.org,10.0.0.15",
    )
    assert settings.trusted_hosts == "api.example.org,10.0.0.15"


def test_external_notification_delivery_is_disabled_by_default():
    settings = make_settings()

    assert settings.notification_email_enabled is False
    assert settings.notification_sms_enabled is False
    assert settings.notification_email_provider == ""
    assert settings.notification_sms_provider == ""


def test_disabled_notification_channels_need_no_provider_credentials():
    settings = make_settings(
        notification_email_enabled=False,
        notification_sms_enabled=False,
    )

    assert settings.notification_email_api_key == ""
    assert settings.notification_sms_api_key == ""


def test_enabled_email_delivery_requires_complete_configuration():
    with pytest.raises(ValidationError, match="Email delivery requires"):
        make_settings(notification_email_enabled=True)


def test_enabled_sms_delivery_requires_complete_configuration():
    with pytest.raises(ValidationError, match="SMS delivery requires"):
        make_settings(notification_sms_enabled=True)


def test_valid_email_delivery_configuration_is_accepted():
    settings = make_settings(
        notification_email_enabled=True,
        notification_email_provider="example-provider",
        notification_email_api_key="test-key",
        notification_email_from="demo@example.org",
        notification_test_email="tester@example.org",
    )

    assert settings.notification_email_enabled is True
    assert settings.notification_email_provider == "example-provider"
    assert settings.notification_test_email == "tester@example.org"


def test_invalid_notification_email_address_is_rejected():
    with pytest.raises(ValidationError, match="email address"):
        make_settings(notification_test_email="not-an-email")


def test_valid_sms_delivery_configuration_is_accepted():
    settings = make_settings(
        notification_sms_enabled=True,
        notification_sms_provider="example-provider",
        notification_sms_api_key="test-key",
        notification_sms_sender_id="HOSPITAL",
        notification_test_phone="+251912345678",
    )

    assert settings.notification_sms_enabled is True
    assert settings.notification_test_phone == "+251912345678"


def test_sample_sms_configuration_needs_no_gateway_credentials():
    settings = make_settings(
        notification_sms_enabled=True,
        notification_sms_provider="sample",
        notification_test_phone="+251900000000",
    )

    assert settings.notification_sms_enabled is True
    assert settings.notification_sms_provider == "sample"
    assert settings.notification_sms_api_key == ""
    assert settings.notification_sms_sender_id == ""


def test_sample_sms_configuration_still_requires_test_recipient():
    with pytest.raises(ValidationError, match="test recipient"):
        make_settings(
            notification_sms_enabled=True,
            notification_sms_provider="sample",
        )


def test_real_sms_provider_still_requires_api_key():
    with pytest.raises(ValidationError, match="API key"):
        make_settings(
            notification_sms_enabled=True,
            notification_sms_provider="real-gateway",
            notification_sms_sender_id="HOSPITAL",
            notification_test_phone="+251900000000",
        )


@pytest.mark.parametrize(
    "phone",
    [
        "0912345678",
        "+251 912345678",
        "+123",
        "not-a-phone",
    ],
)
def test_invalid_notification_test_phone_is_rejected(phone):
    with pytest.raises(ValidationError, match="E.164"):
        make_settings(notification_test_phone=phone)


def test_notification_provider_names_are_normalized():
    settings = make_settings(
        notification_email_provider="  Example_Provider ",
        notification_sms_provider=" SMS-Gateway ",
    )

    assert settings.notification_email_provider == "example_provider"
    assert settings.notification_sms_provider == "sms-gateway"


def test_invalid_notification_provider_name_is_rejected():
    with pytest.raises(ValidationError, match="provider name"):
        make_settings(notification_email_provider="invalid provider name")
