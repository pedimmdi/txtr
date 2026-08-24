"""Smoke tests for OpenAPI schema and documentation UIs."""

import json
import pytest


@pytest.mark.django_db
def test_schema_endpoint_returns_openapi(api_client):
    """GET /api/schema/ must return a valid OpenAPI document."""
    response = api_client.get(
        "/api/schema/",
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 200

    # spectacular may use application/vnd.oai.openapi or application/json
    content_type = response.get("Content-Type", "")
    assert "json" in content_type or "openapi" in content_type

    data = json.loads(response.content.decode("utf-8"))
    assert data.get("openapi", "").startswith("3.")
    assert "paths" in data
    assert "info" in data
    assert data["info"].get("title") == "Txtr API"


@pytest.mark.django_db
def test_swagger_ui_loads(api_client):
    """Swagger UI page must be reachable."""
    response = api_client.get("/api/schema/swagger-ui/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_redoc_loads(api_client):
    """ReDoc page must be reachable."""
    response = api_client.get("/api/schema/redoc/")
    assert response.status_code == 200
