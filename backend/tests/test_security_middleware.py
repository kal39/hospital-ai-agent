from fastapi.testclient import TestClient

from app.main import app


def test_trusted_host_can_access_health_endpoint() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={"Host": "testserver"},
        )

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_untrusted_host_is_rejected() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={"Host": "untrusted.example"},
        )

    assert response.status_code == 400


def test_security_headers_are_added_to_responses() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={"Host": "testserver"},
        )

    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert (
        response.headers["Referrer-Policy"]
        == "strict-origin-when-cross-origin"
    )
    assert (
        response.headers["Permissions-Policy"]
        == "camera=(), microphone=(self), geolocation=()"
    )


def test_untrusted_host_rejection_keeps_cors_headers() -> None:
    with TestClient(app) as client:
        response = client.get(
            "/health",
            headers={
                "Host": "untrusted.example",
                "Origin": "http://localhost:5173",
            },
        )

    assert response.status_code == 400
    assert (
        response.headers.get("access-control-allow-origin")
        == "http://localhost:5173"
    )
