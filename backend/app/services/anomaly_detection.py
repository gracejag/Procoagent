# app/services/anomaly_detection.py
"""
Anomaly Detection Service for Revenue Agent

This service implements statistical algorithms to detect abnormal revenue patterns:
1. Rolling average comparison (7-day, 30-day windows)
2. Standard deviation threshold detection (Z-score)
3. Day-of-week pattern recognition
4. Severity scoring system

Usage:
    from app.services.anomaly_detection import AnomalyDetector
    
    detector = AnomalyDetector(db, business_id)
    anomaly = detector.detect_anomaly()
    
    if anomaly and anomaly["detected"]:
        print(f"Anomaly found: {anomaly['severity']} severity")
"""

import statistics
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.transaction import Transaction


class AnomalyDetector:
    """
    Revenue anomaly detection engine.
    
    Attributes:
        db: SQLAlchemy database session
        business_id: The business to analyze
        threshold_std: Z-score threshold for anomaly detection (default: 2.0)
    """
    
    def __init__(
        self,
        db: Session,
        business_id: int,
        threshold_std: float = 2.0
    ):
        """
        Initialize the anomaly detector.
        
        Args:
            db: Database session
            business_id: Business ID to analyze
            threshold_std: Standard deviation threshold (default: 2.0 = 95% confidence)
        """
        self.db = db
        self.business_id = business_id
        self.threshold_std = threshold_std
    
    def get_daily_totals(self, days: int = 30) -> list[dict]:
        """
        Get daily revenue totals for the past N days.
        
        Args:
            days: Number of days to look back (default: 30)
            
        Returns:
            List of dicts with 'date' and 'revenue' keys, ordered chronologically
        """
        start_date = datetime.utcnow() - timedelta(days=days)
        
        results = self.db.query(
            func.date(Transaction.transaction_date).label("date"),
            func.sum(Transaction.amount).label("revenue")
        ).filter(
            Transaction.business_id == self.business_id,
            Transaction.transaction_date >= start_date
        ).group_by(
            func.date(Transaction.transaction_date)
        ).order_by(
            func.date(Transaction.transaction_date)
        ).all()
        
        return [
            {"date": r.date, "revenue": float(r.revenue) if r.revenue else 0}
            for r in results
        ]
    
    def calculate_rolling_average(self, values: list[float], window: int = 7) -> float:
        """
        Calculate rolling average of the last N values.
        
        Args:
            values: List of revenue values
            window: Number of values to average (default: 7)
            
        Returns:
            Rolling average, or simple average if fewer than window values
        """
        if not values:
            return 0.0
        
        if len(values) < window:
            return sum(values) / len(values)
        
        return sum(values[-window:]) / window
    
    def calculate_std_dev(self, values: list[float]) -> float:
        """
        Calculate standard deviation of values.
        
        Args:
            values: List of revenue values
            
        Returns:
            Standard deviation, or 0 if insufficient data
        """
        if len(values) < 2:
            return 0.0
        
        try:
            return statistics.stdev(values)
        except statistics.StatisticsError:
            return 0.0
    
    def calculate_z_score(
        self,
        value: float,
        mean: float,
        std_dev: float
    ) -> float:
        """
        Calculate Z-score (number of standard deviations from mean).
        
        Args:
            value: The value to score
            mean: The mean to compare against
            std_dev: Standard deviation
            
        Returns:
            Z-score (negative = below average, positive = above average)
        """
        if std_dev == 0:
            return 0.0
        
        return (value - mean) / std_dev
    
    def get_day_of_week_baseline(self, target_dow: int, days: int = 60) -> float:
        """
        Get average revenue for a specific day of week.
        
        Args:
            target_dow: Day of week (0=Monday, 6=Sunday)
            days: Days of history to consider (default: 60)
            
        Returns:
            Average revenue for that day of week
        """
        daily_totals = self.get_daily_totals(days=days)
        
        dow_values = []
        for day_data in daily_totals:
            date = day_data["date"]
            if hasattr(date, "weekday"):
                if date.weekday() == target_dow:
                    dow_values.append(day_data["revenue"])
        
        if not dow_values:
            return 0.0
        
        return sum(dow_values) / len(dow_values)
    
    def detect_anomaly(self, reference_date: Optional[datetime] = None) -> Optional[dict]:
        """
        Detect if there's a revenue anomaly for the given date.
        
        Uses a multi-factor approach:
        1. Compare today's revenue to 7-day rolling average
        2. Check if drop exceeds 2 standard deviations (configurable)
        3. Consider day-of-week patterns
        4. Score severity based on magnitude
        
        Args:
            reference_date: Date to check (default: today)
            
        Returns:
            Dict with anomaly details if detected, None otherwise
            
        Example return:
            {
                "detected": True,
                "today_revenue": 500.00,
                "rolling_avg_7": 1000.00,
                "rolling_avg_30": 950.00,
                "z_score": -2.5,
                "drop_percent": 50.0,
                "severity": "high",
                "dow_adjusted": True,
                "dow_baseline": 800.00
            }
        """
        # Get historical data
        daily_totals = self.get_daily_totals(days=60)
        
        if len(daily_totals) < 7:
            # Not enough data to detect anomalies reliably
            return None
        
        revenues = [d["revenue"] for d in daily_totals]
        
        # Get today's revenue (last entry) and historical (all but last)
        today_revenue = revenues[-1] if revenues else 0
        historical_revenues = revenues[:-1] if len(revenues) > 1 else revenues
        
        # Calculate statistics
        rolling_avg_7 = self.calculate_rolling_average(historical_revenues, 7)
        rolling_avg_30 = self.calculate_rolling_average(historical_revenues, 30)
        std_dev = self.calculate_std_dev(historical_revenues)
        
        # Calculate Z-score
        z_score = self.calculate_z_score(today_revenue, rolling_avg_7, std_dev)
        
        # Check for day-of-week adjustment
        today_date = daily_totals[-1]["date"] if daily_totals else datetime.utcnow().date()
        if hasattr(today_date, "weekday"):
            today_dow = today_date.weekday()
        else:
            today_dow = datetime.utcnow().weekday()
            
        dow_baseline = self.get_day_of_week_baseline(today_dow)
        
        # Calculate drop percentage
        if rolling_avg_7 > 0:
            drop_percent = ((rolling_avg_7 - today_revenue) / rolling_avg_7) * 100
        else:
            drop_percent = 0
        
        # Determine if this is an anomaly
        is_anomaly = z_score < -self.threshold_std and drop_percent > 15
        
        if not is_anomaly:
            return None
        
        # Calculate severity
        severity = self._calculate_severity(z_score, drop_percent)
        
        return {
            "detected": True,
            "today_revenue": today_revenue,
            "rolling_avg_7": rolling_avg_7,
            "rolling_avg_30": rolling_avg_30,
            "z_score": z_score,
            "drop_percent": drop_percent,
            "severity": severity,
            "dow_baseline": dow_baseline,
            "dow_adjusted": dow_baseline > 0,
            "std_dev": std_dev,
            "data_points": len(historical_revenues),
        }
    
    def _calculate_severity(self, z_score: float, drop_percent: float) -> str:
        """
        Calculate anomaly severity based on Z-score and drop percentage.
        
        Severity levels:
        - high: Z-score < -3 OR drop > 40%
        - medium: Z-score < -2 OR drop > 25%
        - low: Everything else that qualified as anomaly
        
        Args:
            z_score: The calculated Z-score
            drop_percent: Percentage drop from average
            
        Returns:
            Severity string: "low", "medium", or "high"
        """
        if z_score < -3 or drop_percent > 40:
            return "high"
        elif z_score < -2 or drop_percent > 25:
            return "medium"
        else:
            return "low"
    
    def get_trend_analysis(self, days: int = 30) -> dict:
        """
        Analyze revenue trends over the specified period.
        
        Returns:
            Dict with trend analysis including:
            - direction: "up", "down", or "stable"
            - change_percent: Percentage change over period
            - volatility: Standard deviation as percentage of mean
        """
        daily_totals = self.get_daily_totals(days=days)
        
        if len(daily_totals) < 7:
            return {
                "direction": "unknown",
                "change_percent": 0,
                "volatility": 0,
                "data_points": len(daily_totals),
            }
        
        revenues = [d["revenue"] for d in daily_totals]
        
        # Compare first week average to last week average
        first_week_avg = self.calculate_rolling_average(revenues[:7], 7)
        last_week_avg = self.calculate_rolling_average(revenues[-7:], 7)
        
        if first_week_avg > 0:
            change_percent = ((last_week_avg - first_week_avg) / first_week_avg) * 100
        else:
            change_percent = 0
        
        # Determine direction
        if change_percent > 5:
            direction = "up"
        elif change_percent < -5:
            direction = "down"
        else:
            direction = "stable"
        
        # Calculate volatility (coefficient of variation)
        mean_revenue = sum(revenues) / len(revenues) if revenues else 0
        std_dev = self.calculate_std_dev(revenues)
        volatility = (std_dev / mean_revenue * 100) if mean_revenue > 0 else 0
        
        return {
            "direction": direction,
            "change_percent": change_percent,
            "volatility": volatility,
            "first_week_avg": first_week_avg,
            "last_week_avg": last_week_avg,
            "data_points": len(revenues),
        }
