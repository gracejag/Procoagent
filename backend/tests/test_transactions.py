"""
Integration tests for transaction upload endpoints
"""

import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import User, Business

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Create tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def auth_headers():
    """Create a test user and return auth headers."""
    # Register user
    client.post(
        "/api/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User",
        },
    )
    
    # Login
    response = client.post(
        "/api/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpassword123",
        },
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_business(auth_headers):
    """Create a test business."""
    response = client.post(
        "/api/businesses",
        json={
            "name": "Test Salon",
            "business_type": "salon",
            "timezone": "America/New_York",
        },
        headers=auth_headers,
    )
    return response.json()


class TestCSVUpload:
    """Tests for CSV file upload endpoint."""

    def test_upload_valid_csv(self, auth_headers, test_business):
        """Test uploading a valid CSV file."""
        csv_content = """transaction_id,timestamp,amount,description,customer_id,payment_method
TXN_001,2026-01-10T10:30:00,50.00,Haircut,CUST_001,card
TXN_002,2026-01-10T11:00:00,75.00,Color,CUST_002,card
TXN_003,2026-01-10T14:30:00,25.00,Blowout,CUST_001,cash"""

        files = {"file": ("transactions.csv", io.StringIO(csv_content), "text/csv")}
        
        response = client.post(
            f"/api/businesses/{test_business['id']}/transactions/upload",
            files=files,
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["imported_count"] == 3
        assert data["errors"] == []

    def test_upload_csv_with_invalid_rows(self, auth_headers, test_business):
        """Test CSV with some invalid rows - should import valid ones."""
        csv_content = """transaction_id,timestamp,amount,description,customer_id,payment_method
TXN_001,2026-01-10T10:30:00,50.00,Haircut,CUST_001,card
TXN_002,invalid-date,75.00,Color,CUST_002,card
TXN_003,2026-01-10T14:30:00,not-a-number,Blowout,CUST_001,cash
TXN_004,2026-01-10T15:00:00,30.00,Trim,CUST_003,card"""

        files = {"file": ("transactions.csv", io.StringIO(csv_content), "text/csv")}
        
        response = client.post(
            f"/api/businesses/{test_business['id']}/transactions/upload",
            files=files,
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["imported_count"] == 2  # Only valid rows
        assert len(data["errors"]) == 2  # Two invalid rows

    def test_upload_empty_csv(self, auth_headers, test_business):
        """Test uploading an empty CSV."""
        csv_content = """transaction_id,timestamp,amount,description,customer_id,payment_method"""

        files = {"file": ("empty.csv", io.StringIO(csv_content), "text/csv")}
        
        response = client.post(
            f"/api/businesses/{test_business['id']}/transactions/upload",
            files=files,
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["imported_count"] == 0

    def test_upload_csv_missing_headers(self, auth_headers, test_business):
        """Test CSV with missing required headers."""
        csv_content = """transaction_id,amount
TXN_001,50.00"""

        files = {"file": ("bad.csv", io.StringIO(csv_content), "text/csv")}
        
        response = client.post(
            f"/api/businesses/{test_business['id']}/transactions/upload",
            files=files,
            headers=auth_headers,
        )
        
        assert response.status_code == 400
        assert "missing required columns" in response.json()["detail"].lower()

    def test_upload_without_auth(self, test_business):
        """Test upload fails without authentication."""
        csv_content = """transaction_id,timestamp,amount,description,customer_id,payment_method
TXN_001,2026-01-10T10:30:00,50.00,Haircut,CUST_001,card"""

        files = {"file": ("transactions.csv", io.StringIO(csv_content), "text/csv")}
        
        response = client.post(
            f"/api/businesses/{test_business['id']}/transactions/upload",
            files=files,
        )
        
        assert response.status_code == 401


class TestManualTransactionEntry:
    """Tests for manual transaction entry endpoint."""

    def test_create_single_transaction(self, auth_headers, test_business):
        """Test creating a single transaction manually."""
        response = client.post(
            f"/api/businesses/{test_business['id']}/transactions",
            json={
                "amount": 65.00,
                "description": "Haircut and style",
                "customer_id": "CUST_NEW",
                "payment_method": "card",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["amount"] == 65.00
        assert data["description"] == "Haircut and style"
        assert "id" in data
        assert "timestamp" in data

    def test_create_transaction_invalid_amount(self, auth_headers, test_business):
        """Test that negative amounts are rejected."""
        response = client.post(
            f"/api/businesses/{test_business['id']}/transactions",
            json={
                "amount": -50.00,
                "description": "Invalid",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 422  # Validation error


class TestTransactionRetrieval:
    """Tests for retrieving transactions."""

    def test_get_transactions_paginated(self, auth_headers, test_business):
        """Test paginated transaction retrieval."""
        # First, add some transactions
        for i in range(15):
            client.post(
                f"/api/businesses/{test_business['id']}/transactions",
                json={"amount": 10.00 + i, "description": f"Transaction {i}"},
                headers=auth_headers,
            )
        
        # Get first page
        response = client.get(
            f"/api/businesses/{test_business['id']}/transactions?limit=10&offset=0",
            headers=auth_headers,
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 10
        assert data["total"] == 15

    def test_get_transactions_date_filter(self, auth_headers, test_business):
        """Test filtering transactions by date range."""
        response = client.get(
            f"/api/businesses/{test_business['id']}/transactions",
            params={
                "start_date": "2026-01-01",
                "end_date": "2026-01-31",
            },
            headers=auth_headers,
        )
        
        assert response.status_code == 200
