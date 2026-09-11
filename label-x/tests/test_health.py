"""Phase 1 tests: health endpoint, root endpoint, error envelope, schema import."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["app_name"]
    assert body["version"]
    assert body["environment"]


def test_root_returns_service_info() -> None:
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["service"]
    assert body["docs"] == "/docs"
    assert body["health"] == "/health"


def test_unknown_route_returns_standard_error_envelope() -> None:
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404
    body = response.json()
    assert body["error"] == "http_error"
    assert body["status_code"] == 404
    assert "detail" in body


def test_shared_schemas_are_importable() -> None:
    from schemas.common import ErrorResponse, HealthStatus

    health = HealthStatus(status="ok", app_name="x", version="0.1.0", environment="test")
    error = ErrorResponse(error="http_error", detail="not found", status_code=404)
    assert health.status == "ok"
    assert error.status_code == 404
