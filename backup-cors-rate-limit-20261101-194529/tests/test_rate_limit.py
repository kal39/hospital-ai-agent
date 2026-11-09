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
