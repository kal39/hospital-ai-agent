from fastapi.testclient import TestClient

from app.main import app
from app.core.config import get_settings


def test_rate_limit_blocks_excess_requests(monkeypatch):
    settings = get_settings()

    monkeypatch.setattr(settings, "rate_limit_max_requests", 3)
    monkeypatch.setattr(settings, "rate_limit_window_ms", 60000)

    with TestClient(app) as client:
        headers = {"X-Demo-Patient-Id": "patient-001"}

        for _ in range(3):
            response = client.get(
                "/api/appointments/departments",
                headers=headers,
            )
            assert response.status_code == 200

        blocked = client.get(
            "/api/appointments/departments",
            headers=headers,
        )

        assert blocked.status_code == 429
        assert blocked.headers["retry-after"] == "60"


def test_rotating_demo_patient_header_does_not_bypass_limit(monkeypatch):
    settings = get_settings()

    monkeypatch.setattr(settings, "rate_limit_max_requests", 2)
    monkeypatch.setattr(settings, "rate_limit_window_ms", 60000)

    with TestClient(app) as client:
        first = client.get(
            "/api/appointments/departments",
            headers={"X-Demo-Patient-Id": "patient-001"},
        )
        second = client.get(
            "/api/appointments/departments",
            headers={"X-Demo-Patient-Id": "patient-002"},
        )
        third = client.get(
            "/api/appointments/departments",
            headers={"X-Demo-Patient-Id": "patient-999"},
        )

        assert first.status_code == 200
        assert second.status_code == 200
        assert third.status_code == 429


def test_health_endpoint_not_rate_limited(monkeypatch):
    settings = get_settings()

    monkeypatch.setattr(settings, "rate_limit_max_requests", 1)

    with TestClient(app) as client:
        assert client.get("/health").status_code == 200
        assert client.get("/health").status_code == 200
        assert client.get("/health").status_code == 200

def test_expired_inactive_ip_histories_are_pruned():
    from collections import deque
    from app.core.rate_limit import (
        _lock,
        _requests,
        _prune_expired_requests_locked,
        reset_rate_limit_state,
    )

    reset_rate_limit_state()

    with _lock:
        _requests["ip:inactive"] = deque([1.0, 2.0])
        _requests["ip:active"] = deque([95.0, 99.0])

        _prune_expired_requests_locked(now=100.0, window=10.0)

        assert "ip:inactive" not in _requests
        assert list(_requests["ip:active"]) == [95.0, 99.0]

    reset_rate_limit_state()

def test_rate_limited_response_includes_cors_headers_for_allowed_origin(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "rate_limit_max_requests", 1)
    monkeypatch.setattr(settings, "rate_limit_window_ms", 60000)

    with TestClient(app, client=("192.0.2.20", 12345)) as client:
        headers = {"Origin": "http://localhost:5173"}

        first = client.get("/api/appointments/departments", headers=headers)
        second = client.get("/api/appointments/departments", headers=headers)

        assert first.status_code == 401
        assert second.status_code == 429
        assert second.headers["retry-after"] == "60"
        assert (
            second.headers.get("access-control-allow-origin")
            == "http://localhost:5173"
        )
        assert second.headers.get("access-control-allow-credentials") == "true"


def test_disallowed_origin_does_not_receive_cors_permission():
    with TestClient(app, client=("192.0.2.21", 12345)) as client:
        response = client.get(
            "/api/appointments/departments",
            headers={"Origin": "https://untrusted.example"},
        )

        assert response.status_code == 401
        assert "access-control-allow-origin" not in response.headers


def test_allowed_cors_preflight_request_succeeds():
    with TestClient(app, client=("192.0.2.22", 12345)) as client:
        response = client.options(
            "/api/appointments/departments",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "x-demo-patient-id",
            },
        )

        assert response.status_code == 200
        assert (
            response.headers.get("access-control-allow-origin")
            == "http://localhost:5173"
        )
        assert "GET" in response.headers.get("access-control-allow-methods", "")
        assert (
            "x-demo-patient-id"
            in response.headers.get("access-control-allow-headers", "").lower()
        )


def test_separate_client_ips_have_independent_rate_limits(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "rate_limit_max_requests", 1)
    monkeypatch.setattr(settings, "rate_limit_window_ms", 60000)

    with (
        TestClient(app, client=("192.0.2.30", 12345)) as first_client,
        TestClient(app, client=("192.0.2.31", 12345)) as second_client,
    ):
        first = first_client.get("/api/appointments/departments")
        first_again = first_client.get("/api/appointments/departments")
        second = second_client.get("/api/appointments/departments")

        assert first.status_code == 401
        assert first_again.status_code == 429
        assert second.status_code == 401
