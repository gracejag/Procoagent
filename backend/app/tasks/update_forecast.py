# app/tasks/update_forecast.py
"""
Celery Tasks for Forecast Updates

This module contains background tasks that run daily to:
1. Update revenue forecasts for all businesses
2. Refresh baseline statistics used for anomaly detection
3. Recalculate seasonal patterns
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from celery import shared_task

from ..celery_app import celery_app
from ..database import SessionLocal
from ..models.business import Business
from ..services.anomaly_detection import AnomalyDetector

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def update_all_forecasts(self) -> dict:
    """
    Main scheduled task: Update forecasts for all active businesses.
    Runs daily at 2 AM UTC.
    
    Returns:
        dict: Summary of forecast updates
    """
    db = SessionLocal()
    results = {
        "updated": 0,
        "skipped": 0,
        "errors": 0,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    try:
        # Get all active businesses
        businesses = db.query(Business).filter(Business.is_active == True).all()
        
        for business in businesses:
            try:
                # Queue forecast update for each business
                update_business_forecast.delay(business.id)
                results["updated"] += 1
            except Exception as e:
                logger.error(f"Error queueing forecast update for business {business.id}: {e}")
                results["errors"] += 1
                
        logger.info(f"Queued forecast updates for {results['updated']} businesses")
        
    except Exception as e:
        logger.error(f"Error in update_all_forecasts: {e}")
        self.retry(exc=e)
    finally:
        db.close()
    
    return results


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def update_business_forecast(self, business_id: int) -> dict:
    """
    Update forecast and baseline statistics for a single business.
    
    This task:
    1. Recalculates rolling averages
    2. Updates day-of-week baselines
    3. Refreshes seasonal patterns (if enough data)
    
    Args:
        business_id: The ID of the business to update
        
    Returns:
        dict: Forecast update results
    """
    db = SessionLocal()
    result = {
        "business_id": business_id,
        "success": False,
        "metrics_updated": [],
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    try:
        # Initialize anomaly detector to access calculation methods
        detector = AnomalyDetector(db, business_id)
        
        # Get daily totals for the past 90 days
        daily_totals = detector.get_daily_totals(days=90)
        
        if len(daily_totals) < 7:
            result["skipped"] = True
            result["reason"] = "Insufficient data (need at least 7 days)"
            logger.info(f"Skipping forecast for business {business_id}: insufficient data")
            return result
        
        revenues = [d["revenue"] for d in daily_totals]
        
        # Calculate updated metrics
        metrics = {
            "rolling_avg_7": detector.calculate_rolling_average(revenues, 7),
            "rolling_avg_30": detector.calculate_rolling_average(revenues, 30),
            "std_dev": detector.calculate_std_dev(revenues),
            "data_points": len(revenues),
        }
        
        # Calculate day-of-week baselines
        dow_baselines = calculate_dow_baselines(daily_totals)
        metrics["dow_baselines"] = dow_baselines
        
        # Store metrics (you could save these to a separate table or cache)
        # For now, we just log them
        result["success"] = True
        result["metrics"] = metrics
        result["metrics_updated"] = list(metrics.keys())
        
        logger.info(
            f"Updated forecast for business {business_id}: "
            f"7-day avg=${metrics['rolling_avg_7']:.2f}, "
            f"30-day avg=${metrics['rolling_avg_30']:.2f}"
        )
        
    except Exception as e:
        logger.error(f"Error updating forecast for business {business_id}: {e}")
        result["error"] = str(e)
        self.retry(exc=e)
    finally:
        db.close()
    
    return result


def calculate_dow_baselines(daily_totals: list[dict]) -> dict:
    """
    Calculate day-of-week baseline averages.
    
    Args:
        daily_totals: List of daily revenue data with dates
        
    Returns:
        dict: Average revenue for each day of week (0=Monday, 6=Sunday)
    """
    from collections import defaultdict
    
    dow_totals = defaultdict(list)
    
    for day_data in daily_totals:
        date = day_data.get("date")
        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        elif hasattr(date, "weekday"):
            pass  # Already a date object
        else:
            continue
            
        dow = date.weekday()  # 0=Monday, 6=Sunday
        dow_totals[dow].append(day_data["revenue"])
    
    dow_baselines = {}
    dow_names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    
    for dow in range(7):
        values = dow_totals[dow]
        if values:
            dow_baselines[dow_names[dow]] = sum(values) / len(values)
        else:
            dow_baselines[dow_names[dow]] = 0
    
    return dow_baselines


@celery_app.task(bind=True)
def calculate_seasonal_patterns(self, business_id: int) -> dict:
    """
    Calculate seasonal patterns for a business (if enough historical data).
    Requires at least 3 months of data for meaningful patterns.
    
    This is a more advanced analysis that looks at:
    - Month-over-month trends
    - Holiday effects
    - Seasonal revenue patterns
    
    Args:
        business_id: The business ID
        
    Returns:
        dict: Seasonal pattern analysis
    """
    db = SessionLocal()
    result = {
        "business_id": business_id,
        "has_seasonal_data": False,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    try:
        detector = AnomalyDetector(db, business_id)
        daily_totals = detector.get_daily_totals(days=365)  # Get up to 1 year
        
        if len(daily_totals) < 90:  # Need at least 3 months
            result["reason"] = "Insufficient data for seasonal analysis"
            return result
        
        # Group by month
        from collections import defaultdict
        monthly_totals = defaultdict(list)
        
        for day_data in daily_totals:
            date = day_data.get("date")
            if isinstance(date, str):
                date = datetime.fromisoformat(date)
            month_key = date.strftime("%Y-%m")
            monthly_totals[month_key].append(day_data["revenue"])
        
        # Calculate monthly averages
        monthly_avgs = {
            month: sum(values) / len(values)
            for month, values in monthly_totals.items()
        }
        
        result["has_seasonal_data"] = True
        result["monthly_averages"] = monthly_avgs
        result["months_of_data"] = len(monthly_avgs)
        
        logger.info(f"Calculated seasonal patterns for business {business_id}: {len(monthly_avgs)} months")
        
    except Exception as e:
        logger.error(f"Error calculating seasonal patterns for business {business_id}: {e}")
        result["error"] = str(e)
    finally:
        db.close()
    
    return result
