# app/routers/notifications.py
"""
Notification Preferences API Routes

Endpoints for managing user notification preferences and testing notifications.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import time

from ..database import get_db
from ..models.notification_preferences import NotificationPreferences
from ..models.user import User
from ..services.auth import get_current_user
from ..services.notifications import NotificationService

router = APIRouter(prefix="/notifications", tags=["Notifications"])


# Pydantic schemas
class NotificationPreferencesCreate(BaseModel):
    email_enabled: bool = True
    sms_enabled: bool = False
    phone_number: Optional[str] = None
    min_severity: str = "medium"
    quiet_hours_enabled: bool = False
    quiet_hours_start: Optional[str] = "22:00"
    quiet_hours_end: Optional[str] = "08:00"
    weekly_summary: bool = True


class NotificationPreferencesUpdate(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    phone_number: Optional[str] = None
    min_severity: Optional[str] = None
    quiet_hours_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None
    weekly_summary: Optional[bool] = None


class NotificationPreferencesResponse(BaseModel):
    id: int
    user_id: int
    email_enabled: bool
    sms_enabled: bool
    phone_number: Optional[str]
    min_severity: str
    quiet_hours_enabled: bool
    quiet_hours_start: Optional[str]
    quiet_hours_end: Optional[str]
    weekly_summary: bool

    class Config:
        from_attributes = True


class TestEmailRequest(BaseModel):
    to_email: EmailStr


class TestSMSRequest(BaseModel):
    to_phone: str


# Routes
@router.get("/preferences", response_model=NotificationPreferencesResponse)
def get_preferences(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's notification preferences."""
    prefs = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == current_user.id
    ).first()
    
    if not prefs:
        # Create default preferences
        prefs = NotificationPreferences(user_id=current_user.id)
        db.add(prefs)
        db.commit()
        db.refresh(prefs)
    
    return _prefs_to_response(prefs)


@router.put("/preferences", response_model=NotificationPreferencesResponse)
def update_preferences(
    updates: NotificationPreferencesUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update notification preferences."""
    prefs = db.query(NotificationPreferences).filter(
        NotificationPreferences.user_id == current_user.id
    ).first()
    
    if not prefs:
        prefs = NotificationPreferences(user_id=current_user.id)
        db.add(prefs)
    
    # Update fields
    update_data = updates.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field in ["quiet_hours_start", "quiet_hours_end"] and value:
            # Convert string to time object
            hours, minutes = map(int, value.split(":"))
            value = time(hours, minutes)
        setattr(prefs, field, value)
    
    db.commit()
    db.refresh(prefs)
    
    return _prefs_to_response(prefs)


@router.post("/test/email")
def test_email_notification(
    request: TestEmailRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a test email notification."""
    service = NotificationService()
    
    test_alert = {
        "title": "Test Alert - Revenue Drop",
        "description": "This is a test notification from Revenue Agent.",
        "severity": "medium",
        "data": {
            "today_revenue": 750.00,
            "rolling_avg_7": 1000.00,
            "drop_percent": 25.0,
        }
    }
    
    success = service.send_email_alert(request.to_email, test_alert)
    
    if success:
        return {"message": f"Test email sent to {request.to_email}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test email. Check SendGrid configuration."
        )


@router.post("/test/sms")
def test_sms_notification(
    request: TestSMSRequest,
    current_user: User = Depends(get_current_user)
):
    """Send a test SMS notification."""
    service = NotificationService()
    
    test_alert = {
        "title": "Test Alert",
        "severity": "medium",
        "data": {
            "today_revenue": 750.00,
            "drop_percent": 25.0,
        }
    }
    
    success = service.send_sms_alert(request.to_phone, test_alert)
    
    if success:
        return {"message": f"Test SMS sent to {request.to_phone}"}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send test SMS. Check Twilio configuration."
        )


def _prefs_to_response(prefs: NotificationPreferences) -> dict:
    """Convert preferences to response format."""
    return {
        "id": prefs.id,
        "user_id": prefs.user_id,
        "email_enabled": prefs.email_enabled,
        "sms_enabled": prefs.sms_enabled,
        "phone_number": prefs.phone_number,
        "min_severity": prefs.min_severity,
        "quiet_hours_enabled": prefs.quiet_hours_enabled,
        "quiet_hours_start": prefs.quiet_hours_start.strftime("%H:%M") if prefs.quiet_hours_start else None,
        "quiet_hours_end": prefs.quiet_hours_end.strftime("%H:%M") if prefs.quiet_hours_end else None,
        "weekly_summary": prefs.weekly_summary,
    }
