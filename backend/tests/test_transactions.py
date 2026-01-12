"""
Integration tests for Procoagent API
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test basic app functionality."""

    def test_health_check(self):
        """Test health endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data


class TestBusinessEndpoints:
    """Test business endpoints."""

    def test_business_endpoint_requires_auth(self):
        """Test that business endpoint requires authentication."""
        response = client.get("/business")
        # Should return 401 Unauthorized without token
        assert response.status_code == 401


class TestDocs:
    """Test API documentation."""

    def test_docs_available(self):
        """Test that API docs are accessible."""
        response = client.get("/docs")
        assert response.status_code == 200
