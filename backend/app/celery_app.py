# app/celery_app.py
"""
Celery Configuration for Revenue Agent
Uses Upstash Redis as the broker and backend.

Setup Instructions:
1. Create an Upstash Redis database at https://console.upstash.com/
2. Get your Redis URL (looks like: redis://default:xxx@xxx.upstash.io:6379)
3. Add REDIS_URL to your .env file
"""

from celery import Celery
from celery.schedules import crontab
from .config import settings

# Initialize Celery with Redis broker
celery_app = Celery(
    "revenue_agent",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.check_anomalies",
        "app.tasks.update_forecast",
    ]
)

# Celery Configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task execution settings
    task_acks_late=True,  # Acknowledge task after completion (safer)
    task_reject_on_worker_lost=True,  # Re-queue if worker dies
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Rate limiting (important for free tier)
    task_default_rate_limit="10/m",  # 10 tasks per minute default
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute between retries
    task_max_retries=3,
    
    # Worker settings for Railway (single worker typically)
    worker_prefetch_multiplier=1,  # Don't prefetch too many tasks
    worker_concurrency=2,  # 2 concurrent tasks max
)

# Celery Beat Schedule - Periodic Tasks
celery_app.conf.beat_schedule = {
    # Run anomaly check every hour
    "check-anomalies-hourly": {
        "task": "app.tasks.check_anomalies.check_all_businesses",
        "schedule": crontab(minute=0),  # Every hour at :00
        "options": {"queue": "anomaly"},
    },
    
    # Update forecasts daily at 2 AM UTC
    "update-forecasts-daily": {
        "task": "app.tasks.update_forecast.update_all_forecasts",
        "schedule": crontab(hour=2, minute=0),
        "options": {"queue": "forecast"},
    },
    
    # Quick health check every 15 minutes
    "health-check": {
        "task": "app.tasks.check_anomalies.health_check",
        "schedule": crontab(minute="*/15"),
        "options": {"queue": "default"},
    },
}

# Task routing (optional - helps organize tasks)
celery_app.conf.task_routes = {
    "app.tasks.check_anomalies.*": {"queue": "anomaly"},
    "app.tasks.update_forecast.*": {"queue": "forecast"},
}
