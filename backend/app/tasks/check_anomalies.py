# app/tasks/check_anomalies.py
"""
Celery Tasks for Anomaly Detection

This module contains background tasks that run on a schedule to:
1. Check all businesses for revenue anomalies
2. Generate alerts when anomalies are detected
3. Queue diagnoses for the AI engine
"""

import logging
from datetime import datetime, timedelta
from typing import Optional
from celery import shared_task

from ..celery_app import celery_app
from ..database import SessionLocal
from ..services.anomaly_detection import AnomalyDetector
from ..models.business import Business
from ..models.alert import Alert

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def health_check(self) -> dict:
    """
    Simple health check task to verify Celery is working.
    Runs every 15 minutes.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "worker": self.request.hostname,
    }


@celery_app.task(bind=True, max_retries=3, default_retry_delay=300)
def check_all_businesses(self) -> dict:
    """
    Main scheduled task: Check all active businesses for anomalies.
    Runs every hour at :00.
    
    Returns:
        dict: Summary of anomalies found and alerts created
    """
    db = SessionLocal()
    results = {
        "checked": 0,
        "anomalies_found": 0,
        "alerts_created": 0,
        "errors": 0,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    try:
        # Get all active businesses
        businesses = db.query(Business).filter(Business.is_active == True).all()
        results["checked"] = len(businesses)
        
        for business in businesses:
            try:
                # Check this business for anomalies
                check_business_anomaly.delay(business.id)
            except Exception as e:
                logger.error(f"Error queueing anomaly check for business {business.id}: {e}")
                results["errors"] += 1
                
        logger.info(f"Queued anomaly checks for {len(businesses)} businesses")
        
    except Exception as e:
        logger.error(f"Error in check_all_businesses: {e}")
        self.retry(exc=e)
    finally:
        db.close()
    
    return results


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def check_business_anomaly(self, business_id: int) -> dict:
    """
    Check a single business for revenue anomalies.
    
    Args:
        business_id: The ID of the business to check
        
    Returns:
        dict: Anomaly detection results
    """
    db = SessionLocal()
    result = {
        "business_id": business_id,
        "anomaly_detected": False,
        "alert_created": False,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    try:
        # Initialize anomaly detector
        detector = AnomalyDetector(db, business_id)
        
        # Run detection
        anomaly = detector.detect_anomaly()
        
        if anomaly and anomaly.get("detected"):
            result["anomaly_detected"] = True
            result["severity"] = anomaly.get("severity", "medium")
            result["drop_percent"] = anomaly.get("drop_percent", 0)
            result["z_score"] = anomaly.get("z_score", 0)
            
            # Create alert if anomaly is significant
            if anomaly.get("severity") in ["medium", "high"]:
                alert = create_alert_from_anomaly(db, business_id, anomaly)
                if alert:
                    result["alert_created"] = True
                    result["alert_id"] = alert.id
                    
            logger.info(
                f"Anomaly detected for business {business_id}: "
                f"{anomaly.get('severity')} severity, {anomaly.get('drop_percent'):.1f}% drop"
            )
        else:
            logger.debug(f"No anomaly detected for business {business_id}")
            
    except Exception as e:
        logger.error(f"Error checking anomaly for business {business_id}: {e}")
        result["error"] = str(e)
        self.retry(exc=e)
    finally:
        db.close()
    
    return result


def create_alert_from_anomaly(db, business_id: int, anomaly: dict) -> Optional[Alert]:
    """
    Create an alert record from detected anomaly.
    
    Args:
        db: Database session
        business_id: The business ID
        anomaly: Anomaly detection results
        
    Returns:
        Alert object if created, None otherwise
    """
    try:
        # Check if there's already an unresolved alert for this business today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        existing_alert = db.query(Alert).filter(
            Alert.business_id == business_id,
            Alert.created_at >= today_start,
            Alert.status.in_(["pending", "acknowledged"])
        ).first()
        
        if existing_alert:
            logger.info(f"Alert already exists for business {business_id} today")
            return None
        
        # Create new alert
        alert = Alert(
            business_id=business_id,
            alert_type="revenue_drop",
            severity=anomaly.get("severity", "medium"),
            title=f"Revenue Drop Detected: {anomaly.get('drop_percent', 0):.1f}% below average",
            description=(
                f"Today's revenue is {anomaly.get('drop_percent', 0):.1f}% below the 7-day average. "
                f"Current: ${anomaly.get('today_revenue', 0):.2f}, "
                f"Expected: ${anomaly.get('rolling_avg_7', 0):.2f}"
            ),
            data={
                "today_revenue": anomaly.get("today_revenue"),
                "rolling_avg_7": anomaly.get("rolling_avg_7"),
                "rolling_avg_30": anomaly.get("rolling_avg_30"),
                "z_score": anomaly.get("z_score"),
                "drop_percent": anomaly.get("drop_percent"),
            },
            status="pending",
        )
        
        db.add(alert)
        db.commit()
        db.refresh(alert)
        
        logger.info(f"Created alert {alert.id} for business {business_id}")
        return alert
        
    except Exception as e:
        logger.error(f"Error creating alert for business {business_id}: {e}")
        db.rollback()
        return None


@celery_app.task(bind=True)
def trigger_diagnosis(self, alert_id: int) -> dict:
    """
    Trigger AI diagnosis for an alert.
    This is called after an alert is created.
    
    Args:
        alert_id: The alert ID to diagnose
        
    Returns:
        dict: Diagnosis task result
    """
    # This will be implemented in Phase 3 with Claude API integration
    # For now, just log that we would trigger a diagnosis
    logger.info(f"Would trigger diagnosis for alert {alert_id}")
    return {
        "alert_id": alert_id,
        "status": "diagnosis_pending",
        "timestamp": datetime.utcnow().isoformat(),
    }
