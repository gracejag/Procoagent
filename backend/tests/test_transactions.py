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


class TestAuthEndpoints:
    """Test authentication endpoints."""

    def test_register_endpoint_accepts_post(self):
        """Test register endpoint accepts POST requests."""
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "testpassword123",
                "full_name": "Test User",
            },
        )
        # Should not be 404 (endpoint exists) or 405 (method allowed)
        assert response.status_code not in [404, 405]

    def test_login_endpoint_accepts_post(self):
        """Test login endpoint accepts POST requests."""
        response = client.post(
            "/auth/login",
            json={
                "email": "test@example.com",
                "password": "wrongpassword",
            },
        )
        # Should not be 404 or 405
        assert response.status_code not in [404, 405]


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
