# app/models/alert.py
"""
Alert Model for Revenue Agent

Stores alerts generated when revenue anomalies are detected.
Alerts have a lifecycle: pending -> acknowledged -> resolved/dismissed
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from ..database import Base


class Alert(Base):
    """
    Alert model representing a detected revenue anomaly.
    
    Attributes:
        id: Primary key
        business_id: Foreign key to the business
        alert_type: Type of alert (revenue_drop, revenue_spike, trend_change)
        severity: Alert severity (low, medium, high)
        title: Short description of the alert
        description: Detailed description
        data: JSON field with anomaly data (z_score, drop_percent, etc.)
        status: Alert status (pending, acknowledged, resolved, dismissed)
        diagnosis: AI-generated diagnosis (populated in Phase 3)
        recommended_action: AI-generated action recommendation
        created_at: When the alert was created
        acknowledged_at: When user acknowledged the alert
        resolved_at: When the alert was resolved
    """
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    
    # Alert classification
    alert_type = Column(String(50), nullable=False, default="revenue_drop")
    severity = Column(String(20), nullable=False, default="medium")  # low, medium, high
    
    # Alert content
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    
    # Anomaly data (stored as JSON for flexibility)
    data = Column(JSON, nullable=True)
    
    # Alert lifecycle
    status = Column(String(20), nullable=False, default="pending")
    # Status values: pending, acknowledged, resolved, dismissed
    
    # AI diagnosis (populated in Phase 3)
    diagnosis = Column(Text, nullable=True)
    diagnosis_confidence = Column(Integer, nullable=True)  # 0-100
    recommended_action = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    acknowledged_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Track if action was taken
    action_taken = Column(Boolean, default=False)
    action_result = Column(Text, nullable=True)
    
    # Relationship
    business = relationship("Business", back_populates="alerts")

    def __repr__(self):
        return f"<Alert {self.id}: {self.severity} - {self.title[:30]}>"
    
    def acknowledge(self):
        """Mark alert as acknowledged by user."""
        self.status = "acknowledged"
        self.acknowledged_at = datetime.utcnow()
    
    def resolve(self, result: str = None):
        """Mark alert as resolved."""
        self.status = "resolved"
        self.resolved_at = datetime.utcnow()
        if result:
            self.action_result = result
    
    def dismiss(self):
        """Dismiss the alert without action."""
        self.status = "dismissed"
        self.resolved_at = datetime.utcnow()
    
    def to_dict(self):
        """Convert alert to dictionary for API responses."""
        return {
            "id": self.id,
            "business_id": self.business_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "data": self.data,
            "status": self.status,
            "diagnosis": self.diagnosis,
            "diagnosis_confidence": self.diagnosis_confidence,
            "recommended_action": self.recommended_action,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "action_taken": self.action_taken,
        }
