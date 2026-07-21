"""Tests for the FastAPI application."""

from fastapi.testclient import TestClient
from app import app


client = TestClient(app)


class TestHealth:
    def test_health_returns_200(self):
        """This test FAILS because /health references undefined app_version."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_has_status(self):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestItems:
    def test_list_items(self):
        response = client.get("/items")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert data["count"] == 3

    def test_get_item(self):
        response = client.get("/items/1")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Widget"

    def test_get_item_not_found(self):
        response = client.get("/items/999")
        assert response.status_code == 404
