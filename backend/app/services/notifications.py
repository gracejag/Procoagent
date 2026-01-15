# app/services/notifications.py
"""
Notification Service for Revenue Agent

Handles sending alerts via:
- Email (SendGrid)
- SMS (Twilio)

Usage:
    from app.services.notifications import NotificationService
    
    service = NotificationService()
    service.send_email_alert(to_email, alert)
    service.send_sms_alert(to_phone, alert)
"""

import logging
from typing import Optional
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, HtmlContent
from twilio.rest import Client as TwilioClient
from twilio.base.exceptions import TwilioRestException

from ..config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service for sending notifications via email and SMS.
    """
    
    def __init__(self):
        """Initialize notification clients."""
        # SendGrid setup
        self.sendgrid_client = None
        if settings.SENDGRID_API_KEY:
            self.sendgrid_client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        
        # Twilio setup
        self.twilio_client = None
        if settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
            self.twilio_client = TwilioClient(
                settings.TWILIO_ACCOUNT_SID,
                settings.TWILIO_AUTH_TOKEN
            )
    
    def send_email_alert(
        self,
        to_email: str,
        alert: dict,
        template: str = "revenue_drop"
    ) -> bool:
        """
        Send an alert email via SendGrid.
        
        Args:
            to_email: Recipient email address
            alert: Alert data dictionary
            template: Email template to use
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.sendgrid_client:
            logger.warning("SendGrid not configured, skipping email")
            return False
        
        try:
            # Build email content
            subject, html_content = self._build_email_content(alert, template)
            
            message = Mail(
                from_email=Email(settings.SENDGRID_FROM_EMAIL, "Revenue Agent"),
                to_emails=To(to_email),
                subject=subject,
                html_content=HtmlContent(html_content)
            )
            
            response = self.sendgrid_client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Email failed with status {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    def send_sms_alert(
        self,
        to_phone: str,
        alert: dict
    ) -> bool:
        """
        Send an alert SMS via Twilio.
        
        Args:
            to_phone: Recipient phone number (with country code, e.g., +1234567890)
            alert: Alert data dictionary
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.twilio_client:
            logger.warning("Twilio not configured, skipping SMS")
            return False
        
        try:
            # Build SMS content (keep it short - 160 chars ideal)
            body = self._build_sms_content(alert)
            
            message = self.twilio_client.messages.create(
                body=body,
                from_=settings.TWILIO_FROM_NUMBER,
                to=to_phone
            )
            
            if message.sid:
                logger.info(f"SMS sent successfully to {to_phone}, SID: {message.sid}")
                return True
            else:
                logger.error("SMS failed - no SID returned")
                return False
                
        except TwilioRestException as e:
            logger.error(f"Twilio error sending SMS to {to_phone}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error sending SMS to {to_phone}: {e}")
            return False
    
    def _build_email_content(self, alert: dict, template: str) -> tuple[str, str]:
        """
        Build email subject and HTML content based on template.
        
        Args:
            alert: Alert data
            template: Template name
            
        Returns:
            Tuple of (subject, html_content)
        """
        if template == "revenue_drop":
            return self._revenue_drop_email(alert)
        elif template == "weekly_summary":
            return self._weekly_summary_email(alert)
        else:
            return self._generic_alert_email(alert)
    
    def _revenue_drop_email(self, alert: dict) -> tuple[str, str]:
        """Build revenue drop alert email."""
        data = alert.get("data", {})
        severity = alert.get("severity", "medium")
        
        # Severity emoji and color
        severity_config = {
            "high": {"emoji": "🚨", "color": "#DC2626"},
            "medium": {"emoji": "⚠️", "color": "#F59E0B"},
            "low": {"emoji": "📉", "color": "#3B82F6"},
        }
        config = severity_config.get(severity, severity_config["medium"])
        
        subject = f"{config['emoji']} Revenue Alert: {alert.get('title', 'Revenue Drop Detected')}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: {config['color']}; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 20px; border-radius: 0 0 8px 8px; }}
                .metric {{ background-color: white; padding: 15px; margin: 10px 0; border-radius: 6px; border-left: 4px solid {config['color']}; }}
                .metric-label {{ font-size: 12px; color: #6b7280; text-transform: uppercase; }}
                .metric-value {{ font-size: 24px; font-weight: bold; color: #111827; }}
                .cta-button {{ display: inline-block; background-color: {config['color']}; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; }}
                .footer {{ text-align: center; padding: 20px; color: #6b7280; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">{config['emoji']} Revenue Alert</h1>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">{severity.upper()} SEVERITY</p>
                </div>
                <div class="content">
                    <p>{alert.get('description', 'A revenue anomaly has been detected.')}</p>
                    
                    <div class="metric">
                        <div class="metric-label">Today's Revenue</div>
                        <div class="metric-value">${data.get('today_revenue', 0):,.2f}</div>
                    </div>
                    
                    <div class="metric">
                        <div class="metric-label">7-Day Average</div>
                        <div class="metric-value">${data.get('rolling_avg_7', 0):,.2f}</div>
                    </div>
                    
                    <div class="metric">
                        <div class="metric-label">Drop Percentage</div>
                        <div class="metric-value" style="color: {config['color']};">↓ {data.get('drop_percent', 0):.1f}%</div>
                    </div>
                    
                    <a href="#" class="cta-button">View Dashboard</a>
                </div>
                <div class="footer">
                    <p>This alert was generated by Revenue Agent</p>
                    <p>You're receiving this because you enabled revenue alerts.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return subject, html_content
    
    def _weekly_summary_email(self, alert: dict) -> tuple[str, str]:
        """Build weekly summary email."""
        subject = "📊 Your Weekly Revenue Summary"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #3B82F6; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .content {{ background-color: #f9fafb; padding: 20px; border-radius: 0 0 8px 8px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1 style="margin: 0;">📊 Weekly Summary</h1>
                </div>
                <div class="content">
                    <p>Here's your revenue summary for the week.</p>
                    <p>{alert.get('description', '')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return subject, html_content
    
    def _generic_alert_email(self, alert: dict) -> tuple[str, str]:
        """Build generic alert email."""
        subject = f"Revenue Agent Alert: {alert.get('title', 'New Alert')}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: sans-serif; padding: 20px;">
            <h2>{alert.get('title', 'Alert')}</h2>
            <p>{alert.get('description', 'You have a new alert.')}</p>
        </body>
        </html>
        """
        
        return subject, html_content
    
    def _build_sms_content(self, alert: dict) -> str:
        """
        Build SMS content (keep under 160 chars for single SMS).
        
        Args:
            alert: Alert data
            
        Returns:
            SMS message body
        """
        data = alert.get("data", {})
        severity = alert.get("severity", "medium")
        
        severity_emoji = {"high": "🚨", "medium": "⚠️", "low": "📉"}.get(severity, "⚠️")
        
        drop_percent = data.get("drop_percent", 0)
        today_revenue = data.get("today_revenue", 0)
        
        # Keep it short!
        message = (
            f"{severity_emoji} Revenue Alert: "
            f"Down {drop_percent:.0f}% today (${today_revenue:,.0f}). "
            f"Check your dashboard."
        )
        
        return message[:160]  # Ensure max 160 chars


# Convenience functions for direct use
def send_alert_email(to_email: str, alert: dict) -> bool:
    """Send an alert email."""
    service = NotificationService()
    return service.send_email_alert(to_email, alert)


def send_alert_sms(to_phone: str, alert: dict) -> bool:
    """Send an alert SMS."""
    service = NotificationService()
    return service.send_sms_alert(to_phone, alert)
