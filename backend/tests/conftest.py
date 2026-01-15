# tests/conftest.py
"""
Pytest fixtures and configuration for Revenue Agent tests.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock
import random


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    return MagicMock()


@pytest.fixture
def sample_daily_revenues():
    """Generate sample daily revenue data for testing."""
    revenues = []
    base_revenue = 1000
    start_date = datetime.utcnow() - timedelta(days=30)
    
    for i in range(30):
        date = start_date + timedelta(days=i)
        dow_factor = 1.3 if date.weekday() >= 5 else 1.0
        noise = random.uniform(0.85, 1.15)
        revenue = base_revenue * dow_factor * noise
        revenues.append({
            "date": date.date(),
            "revenue": round(revenue, 2)
        })
    
    return revenues


@pytest.fixture
def sample_revenues_with_anomaly():
    """Generate revenue data with a clear anomaly on the last day."""
    revenues = []
    base_revenue = 1000
    start_date = datetime.utcnow() - timedelta(days=30)
    
    for i in range(29):
        date = start_date + timedelta(days=i)
        noise = random.uniform(0.9, 1.1)
        revenue = base_revenue * noise
        revenues.append({
            "date": date.date(),
            "revenue": round(revenue, 2)
        })
    
    # Last day: significant drop (50% of normal)
    last_date = start_date + timedelta(days=29)
    revenues.append({
        "date": last_date.date(),
        "revenue": base_revenue * 0.5
    })
    
    return revenues


@pytest.fixture
def sample_revenues_stable():
    """Generate very stable revenue data (low variance)."""
    revenues = []
    base_revenue = 1000
    start_date = datetime.utcnow() - timedelta(days=30)
    
    for i in range(30):
        date = start_date + timedelta(days=i)
        noise = random.uniform(0.98, 1.02)
        revenue = base_revenue * noise
        revenues.append({
            "date": date.date(),
            "revenue": round(revenue, 2)
        })
    
    return revenues


@pytest.fixture
def sample_revenues_high_variance():
    """Generate revenue data with high variance."""
    revenues = []
    base_revenue = 1000
    start_date = datetime.utcnow() - timedelta(days=30)
    
    for i in range(30):
        date = start_date + timedelta(days=i)
        noise = random.uniform(0.6, 1.4)
        revenue = base_revenue * noise
        revenues.append({
            "date": date.date(),
            "revenue": round(revenue, 2)
        })
    
    return revenues


@pytest.fixture
def sample_revenues_trending_down():
    """Generate revenue data with a clear downward trend."""
    revenues = []
    base_revenue = 1500
    start_date = datetime.utcnow() - timedelta(days=30)
    
    for i in range(30):
        date = start_date + timedelta(days=i)
        trend_factor = 1 - (i * 0.02)
        noise = random.uniform(0.95, 1.05)
        revenue = base_revenue * trend_factor * noise
        revenues.append({
            "date": date.date(),
            "revenue": round(revenue, 2)
        })
    
    return revenues


@pytest.fixture
def sample_revenues_trending_up():
    """Generate revenue data with a clear upward trend."""
    revenues = []
    base_revenue = 500
    start_date = datetime.utcnow() - timedelta(days=30)
    
    for i in range(30):
        date = start_date + timedelta(days=i)
        trend_factor = 1 + (i * 0.02)
        noise = random.uniform(0.95, 1.05)
        revenue = base_revenue * trend_factor * noise
        revenues.append({
            "date": date.date(),
            "revenue": round(revenue, 2)
        })
    
    return revenues


@pytest.fixture
def sample_dow_pattern_revenues():
    """Generate revenue data with strong day-of-week patterns."""
    revenues = []
    weekday_base = 800
    weekend_base = 1500
    start_date = datetime.utcnow() - timedelta(days=30)
    
    for i in range(30):
        date = start_date + timedelta(days=i)
        base = weekend_base if date.weekday() >= 5 else weekday_base
        noise = random.uniform(0.9, 1.1)
        revenue = base * noise
        revenues.append({
            "date": date.date(),
            "revenue": round(revenue, 2)
        })
    
    return revenues


@pytest.fixture
def minimal_revenues():
    """Generate minimal revenue data (less than 7 days)."""
    revenues = []
    base_revenue = 1000
    start_date = datetime.utcnow() - timedelta(days=5)
    
    for i in range(5):
        date = start_date + timedelta(days=i)
        revenues.append({
            "date": date.date(),
            "revenue": base_revenue
        })
    
    return revenues


@pytest.fixture
def empty_revenues():
    """Return empty revenue list for edge case testing."""
    return []