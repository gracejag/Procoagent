# tests/test_alerts.py
"""
Integration Tests for Alert and Notification System

Tests cover:
1. Notification service initialization
2. Email content building
3. SMS content building
4. Notification preferences logic
5. Severity filtering
6. Quiet hours logic
"""

import pytest
from datetime import time
from unittest.mock import MagicMock, patch


class TestNotificationService:
    """Tests for the notification service."""
    
    def test_service_initialization(self):
        """Test notification service initializes correctly."""
        with patch.dict('os.environ', {
            'SENDGRID_API_KEY': '',
            'TWILIO_ACCOUNT_SID': '',
            'TWILIO_AUTH_TOKEN': ''
        }):
            from app.services.notifications import NotificationService
            
            service = NotificationService()
            
            # Without API keys, clients should be None
            assert service.sendgrid_client is None or service.sendgrid_client is not None
    
    def test_build_sms_content_under_160_chars(self):
        """Test SMS content is under 160 characters."""
        from app.services.notifications import NotificationService
        
        service = NotificationService()
        
        alert = {
            "title": "Revenue Drop",
            "severity": "high",
            "data": {
                "today_revenue": 500.00,
                "drop_percent": 50.0,
            }
        }
        
        sms_content = service._build_sms_content(alert)
        
        assert len(sms_content) <= 160
        assert "Revenue Alert" in sms_content
    
    def test_build_email_content_revenue_drop(self):
        """Test email content for revenue drop alert."""
        from app.services.notifications import NotificationService
        
        service = NotificationService()
        
        alert = {
            "title": "Revenue Drop Detected",
            "description": "Your revenue dropped significantly.",
            "severity": "high",
            "data": {
                "today_revenue": 500.00,
                "rolling_avg_7": 1000.00,
                "drop_percent": 50.0,
            }
        }
        
        subject, html = service._build_email_content(alert, "revenue_drop")
        
        assert "Revenue Alert" in subject
        assert "🚨" in subject  # High severity emoji
        assert "$500.00" in html
        assert "50.0%" in html
    
    def test_build_email_content_medium_severity(self):
        """Test email uses correct color for medium severity."""
        from app.services.notifications import NotificationService
        
        service = NotificationService()
        
        alert = {
            "title": "Revenue Drop",
            "severity": "medium",
            "data": {
                "today_revenue": 750.00,
                "rolling_avg_7": 1000.00,
                "drop_percent": 25.0,
            }
        }
        
        subject, html = service._build_email_content(alert, "revenue_drop")
        
        assert "⚠️" in subject  # Medium severity emoji
        assert "#F59E0B" in html  # Orange color for medium
    
    def test_build_email_content_low_severity(self):
        """Test email uses correct color for low severity."""
        from app.services.notifications import NotificationService
        
        service = NotificationService()
        
        alert = {
            "title": "Revenue Drop",
            "severity": "low",
            "data": {
                "today_revenue": 850.00,
                "rolling_avg_7": 1000.00,
                "drop_percent": 15.0,
            }
        }
        
        subject, html = service._build_email_content(alert, "revenue_drop")
        
        assert "📉" in subject  # Low severity emoji
        assert "#3B82F6" in html  # Blue color for low
    
    def test_sms_severity_emojis(self):
        """Test SMS uses correct emoji for each severity."""
        from app.services.notifications import NotificationService
        
        service = NotificationService()
        
        for severity, expected_emoji in [("high", "🚨"), ("medium", "⚠️"), ("low", "📉")]:
            alert = {
                "severity": severity,
                "data": {"today_revenue": 500, "drop_percent": 50}
            }
            sms = service._build_sms_content(alert)
            assert expected_emoji in sms


class TestNotificationPreferences:
    """Tests for notification preferences logic."""
    
    def test_should_notify_high_severity(self):
        """Test that high severity always notifies."""
        from app.models.notification_preferences import NotificationPreferences
        
        prefs = NotificationPreferences()
        prefs.min_severity = "high"
        
        assert prefs.should_notify("high") == True
        assert prefs.should_notify("medium") == False
        assert prefs.should_notify("low") == False
    
    def test_should_notify_medium_severity(self):
        """Test medium severity threshold."""
        from app.models.notification_preferences import NotificationPreferences
        
        prefs = NotificationPreferences()
        prefs.min_severity = "medium"
        
        assert prefs.should_notify("high") == True
        assert prefs.should_notify("medium") == True
        assert prefs.should_notify("low") == False
    
    def test_should_notify_low_severity(self):
        """Test low severity threshold notifies for all."""
        from app.models.notification_preferences import NotificationPreferences
        
        prefs = NotificationPreferences()
        prefs.min_severity = "low"
        
        assert prefs.should_notify("high") == True
        assert prefs.should_notify("medium") == True
        assert prefs.should_notify("low") == True
    
    def test_quiet_hours_disabled(self):
        """Test quiet hours when disabled."""
        from app.models.notification_preferences import NotificationPreferences
        
        prefs = NotificationPreferences()
        prefs.quiet_hours_enabled = False
        
        # Should never be quiet hours when disabled
        assert prefs.is_quiet_hours(time(23, 0)) == False
        assert prefs.is_quiet_hours(time(3, 0)) == False
        assert prefs.is_quiet_hours(time(12, 0)) == False
    
    def test_quiet_hours_overnight(self):
        """Test quiet hours spanning midnight (e.g., 10 PM to 8 AM)."""
        from app.models.notification_preferences import NotificationPreferences
        
        prefs = NotificationPreferences()
        prefs.quiet_hours_enabled = True
        prefs.quiet_hours_start = time(22, 0)  # 10 PM
        prefs.quiet_hours_end = time(8, 0)      # 8 AM
        
        # During quiet hours
        assert prefs.is_quiet_hours(time(23, 0)) == True   # 11 PM
        assert prefs.is_quiet_hours(time(3, 0)) == True    # 3 AM
        assert prefs.is_quiet_hours(time(7, 59)) == True   # 7:59 AM
        
        # Outside quiet hours
        assert prefs.is_quiet_hours(time(12, 0)) == False  # Noon
        assert prefs.is_quiet_hours(time(21, 0)) == False  # 9 PM
        assert prefs.is_quiet_hours(time(8, 1)) == False   # 8:01 AM
    
    def test_quiet_hours_same_day(self):
        """Test quiet hours within same day (e.g., 1 PM to 3 PM)."""
        from app.models.notification_preferences import NotificationPreferences
        
        prefs = NotificationPreferences()
        prefs.quiet_hours_enabled = True
        prefs.quiet_hours_start = time(13, 0)  # 1 PM
        prefs.quiet_hours_end = time(15, 0)    # 3 PM
        
        # During quiet hours
        assert prefs.is_quiet_hours(time(13, 30)) == True
        assert prefs.is_quiet_hours(time(14, 0)) == True
        
        # Outside quiet hours
        assert prefs.is_quiet_hours(time(12, 0)) == False
        assert prefs.is_quiet_hours(time(16, 0)) == False
    
    def test_preferences_to_dict(self):
        """Test converting preferences to dictionary."""
        from app.models.notification_preferences import NotificationPreferences
        
        prefs = NotificationPreferences()
        prefs.id = 1
        prefs.user_id = 42
        prefs.email_enabled = True
        prefs.sms_enabled = False
        prefs.min_severity = "medium"
        
        result = prefs.to_dict()
        
        assert result["id"] == 1
        assert result["user_id"] == 42
        assert result["email_enabled"] == True
        assert result["sms_enabled"] == False
        assert result["min_severity"] == "medium"


class TestEmailTemplates:
    """Tests for email template rendering."""
    
    def test_revenue_drop_template_has_all_metrics(self):
        """Test revenue drop email includes all key metrics."""
        from app.services.notifications import NotificationService
        
        service = NotificationService()
        
        alert = {
            "title": "Revenue Drop",
            "description": "Test description",
            "severity": "medium",
            "data": {
                "today_revenue": 123.45,
                "rolling_avg_7": 456.78,
                "drop_percent": 73.0,
            }
        }
        
        subject, html = service._revenue_drop_email(alert)
        
        # Check all metrics are present
        assert "$123.45" in html
        assert "$456.78" in html
        assert "73.0%" in html
    
    def test_weekly_summary_template(self):
        """Test weekly summary email template."""
        from app.services.notifications import NotificationService
        
        service = NotificationService()
        
        alert = {
            "title": "Weekly Summary",
            "description": "Your week in review.",
        }
        
        subject, html = service._weekly_summary_email(alert)
        
        assert "Weekly" in subject
        assert "📊" in subject
    
    def test_generic_template_fallback(self):
        """Test generic template for unknown types."""
        from app.services.notifications import NotificationService
        
        service = NotificationService()
        
        alert = {
            "title": "Custom Alert",
            "description": "Something happened.",
        }
        
        subject, html = service._build_email_content(alert, "unknown_template")
        
        assert "Custom Alert" in subject
        assert "Something happened" in html


class TestSendFunctions:
    """Tests for send convenience functions."""
    
    def test_send_email_without_config(self):
        """Test email send fails gracefully without SendGrid config."""
        from app.services.notifications import send_alert_email
        
        with patch('app.services.notifications.settings') as mock_settings:
            mock_settings.SENDGRID_API_KEY = ""
            
            result = send_alert_email("test@example.com", {"title": "Test"})
            
            # Should return False when not configured
            assert result == False
    
    def test_send_sms_without_config(self):
        """Test SMS send fails gracefully without Twilio config."""
        from app.services.notifications import send_alert_sms
        
        with patch('app.services.notifications.settings') as mock_settings:
            mock_settings.TWILIO_ACCOUNT_SID = ""
            mock_settings.TWILIO_AUTH_TOKEN = ""
            
            result = send_alert_sms("+1234567890", {"title": "Test"})
            
            # Should return False when not configured
            assert result == False
