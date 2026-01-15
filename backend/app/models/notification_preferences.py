# app/models/notification_preferences.py
"""
Notification Preferences Model

Stores user preferences for how they want to receive alerts:
- Email notifications (on/off)
- SMS notifications (on/off)
- Alert severity thresholds
- Quiet hours
"""

from sqlalchemy import Column, Integer, String, Boolean, Time, ForeignKey
from sqlalchemy.orm import relationship
from datetime import time

from ..database import Base


class NotificationPreferences(Base):
    """
    User notification preferences.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User
        email_enabled: Whether to send email alerts
        sms_enabled: Whether to send SMS alerts
        phone_number: Phone number for SMS (with country code)
        min_severity: Minimum severity to notify (low, medium, high)
        quiet_hours_start: Start of quiet hours (no notifications)
        quiet_hours_end: End of quiet hours
        weekly_summary: Whether to send weekly summary emails
    """
    __tablename__ = "notification_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Notification channels
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=False)
    phone_number = Column(String, nullable=True)  # For SMS, e.g., +14155551234
    
    # Alert filtering
    min_severity = Column(String, default="medium")  # low, medium, high
    
    # Quiet hours (don't send notifications during this time)
    quiet_hours_enabled = Column(Boolean, default=False)
    quiet_hours_start = Column(Time, default=time(22, 0))  # 10 PM
    quiet_hours_end = Column(Time, default=time(8, 0))     # 8 AM
    
    # Summary emails
    weekly_summary = Column(Boolean, default=True)
    
    # Relationship
    user = relationship("User", back_populates="notification_preferences")

    def __repr__(self):
        return f"<NotificationPreferences user_id={self.user_id}>"
    
    def should_notify(self, severity: str) -> bool:
        """
        Check if we should send a notification for this severity level.
        
        Args:
            severity: Alert severity (low, medium, high)
            
        Returns:
            True if notification should be sent
        """
        severity_levels = {"low": 1, "medium": 2, "high": 3}
        min_level = severity_levels.get(self.min_severity, 2)
        alert_level = severity_levels.get(severity, 2)
        
        return alert_level >= min_level
    
    def is_quiet_hours(self, current_time: time) -> bool:
        """
        Check if current time is within quiet hours.
        
        Args:
            current_time: Current time to check
            
        Returns:
            True if in quiet hours
        """
        if not self.quiet_hours_enabled:
            return False
        
        start = self.quiet_hours_start
        end = self.quiet_hours_end
        
        # Handle overnight quiet hours (e.g., 10 PM to 8 AM)
        if start > end:
            return current_time >= start or current_time <= end
        else:
            return start <= current_time <= end
    
    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "email_enabled": self.email_enabled,
            "sms_enabled": self.sms_enabled,
            "phone_number": self.phone_number,
            "min_severity": self.min_severity,
            "quiet_hours_enabled": self.quiet_hours_enabled,
            "quiet_hours_start": self.quiet_hours_start.isoformat() if self.quiet_hours_start else None,
            "quiet_hours_end": self.quiet_hours_end.isoformat() if self.quiet_hours_end else None,
            "weekly_summary": self.weekly_summary,
        }
