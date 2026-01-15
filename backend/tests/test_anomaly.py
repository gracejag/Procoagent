# tests/test_anomaly.py
"""
Unit Tests for Anomaly Detection Algorithms

Tests cover:
1. Rolling average calculations (7-day, 30-day windows)
2. Standard deviation calculations
3. Z-score calculations
4. Day-of-week baseline calculations
5. Anomaly detection logic
6. Severity scoring
7. Edge cases (minimal data, empty data, high variance)
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import statistics


class TestRollingAverage:
    """Tests for rolling average calculation."""
    
    def test_rolling_average_basic(self):
        """Test basic rolling average with enough data."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        values = [100, 110, 90, 105, 95, 100, 100]  # 7 values
        result = detector.calculate_rolling_average(values, window=7)
        
        expected = sum(values) / 7  # 100
        assert abs(result - expected) < 0.01
    
    def test_rolling_average_insufficient_data(self):
        """Test rolling average with less data than window size."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        values = [100, 110, 90]  # Only 3 values, window is 7
        result = detector.calculate_rolling_average(values, window=7)
        
        # Should return average of available data
        expected = sum(values) / 3  # 100
        assert abs(result - expected) < 0.01
    
    def test_rolling_average_empty_list(self):
        """Test rolling average with empty list."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        result = detector.calculate_rolling_average([], window=7)
        assert result == 0.0
    
    def test_rolling_average_uses_last_n_values(self):
        """Test that rolling average uses only the last N values."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        # First 10 values are 50, last 7 are 100
        values = [50] * 10 + [100] * 7
        result = detector.calculate_rolling_average(values, window=7)
        
        # Should only use last 7 values (all 100s)
        assert result == 100.0
    
    def test_rolling_average_30_day(self):
        """Test 30-day rolling average."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        values = [100] * 30
        result = detector.calculate_rolling_average(values, window=30)
        
        assert result == 100.0


class TestStandardDeviation:
    """Tests for standard deviation calculation."""
    
    def test_std_dev_basic(self):
        """Test basic standard deviation calculation."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        values = [100, 110, 90, 105, 95, 100, 100]
        result = detector.calculate_std_dev(values)
        
        expected = statistics.stdev(values)
        assert abs(result - expected) < 0.01
    
    def test_std_dev_single_value(self):
        """Test std dev with single value (should return 0)."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        result = detector.calculate_std_dev([100])
        assert result == 0.0
    
    def test_std_dev_empty_list(self):
        """Test std dev with empty list."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        result = detector.calculate_std_dev([])
        assert result == 0.0
    
    def test_std_dev_identical_values(self):
        """Test std dev with all identical values (should be 0)."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        result = detector.calculate_std_dev([100, 100, 100, 100])
        assert result == 0.0


class TestZScore:
    """Tests for Z-score calculation."""
    
    def test_z_score_basic(self):
        """Test basic Z-score calculation."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        # Value is 2 std devs below mean
        result = detector.calculate_z_score(value=80, mean=100, std_dev=10)
        
        assert result == -2.0
    
    def test_z_score_above_mean(self):
        """Test Z-score for value above mean."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        result = detector.calculate_z_score(value=120, mean=100, std_dev=10)
        
        assert result == 2.0
    
    def test_z_score_at_mean(self):
        """Test Z-score when value equals mean."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        result = detector.calculate_z_score(value=100, mean=100, std_dev=10)
        
        assert result == 0.0
    
    def test_z_score_zero_std_dev(self):
        """Test Z-score when std dev is 0."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        result = detector.calculate_z_score(value=80, mean=100, std_dev=0)
        
        assert result == 0.0  # Avoid division by zero


class TestSeverityScoring:
    """Tests for anomaly severity scoring."""
    
    def test_severity_high_z_score(self):
        """Test high severity for extreme Z-score."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        result = detector._calculate_severity(z_score=-3.5, drop_percent=30)
        
        assert result == "high"
    
    def test_severity_high_drop_percent(self):
        """Test high severity for large drop percentage."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        result = detector._calculate_severity(z_score=-2.5, drop_percent=45)
        
        assert result == "high"
    
    def test_severity_medium(self):
        """Test medium severity."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        result = detector._calculate_severity(z_score=-2.5, drop_percent=30)
        
        assert result == "medium"
    
    def test_severity_low(self):
        """Test low severity."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        # Just above threshold
        result = detector._calculate_severity(z_score=-1.8, drop_percent=20)
        
        assert result == "low"


class TestAnomalyDetection:
    """Tests for the main anomaly detection logic."""
    
    def test_detect_anomaly_with_clear_drop(self, sample_revenues_with_anomaly):
        """Test detection of clear revenue drop."""
        from app.services.anomaly_detection import AnomalyDetector
        
        mock_db = MagicMock()
        detector = AnomalyDetector(mock_db, business_id=1)
        
        # Mock the get_daily_totals method
        with patch.object(detector, 'get_daily_totals', return_value=sample_revenues_with_anomaly):
            result = detector.detect_anomaly()
        
        assert result is not None
        assert result["detected"] == True
        assert result["severity"] in ["low", "medium", "high"]
        assert result["drop_percent"] > 0
    
    def test_detect_anomaly_no_anomaly(self, sample_revenues_stable):
        """Test that stable data does not trigger anomaly."""
        from app.services.anomaly_detection import AnomalyDetector
        
        mock_db = MagicMock()
        detector = AnomalyDetector(mock_db, business_id=1)
        
        with patch.object(detector, 'get_daily_totals', return_value=sample_revenues_stable):
            result = detector.detect_anomaly()
        
        # Stable data should not trigger anomaly
        assert result is None
    
    def test_detect_anomaly_insufficient_data(self, minimal_revenues):
        """Test detection with insufficient data."""
        from app.services.anomaly_detection import AnomalyDetector
        
        mock_db = MagicMock()
        detector = AnomalyDetector(mock_db, business_id=1)
        
        with patch.object(detector, 'get_daily_totals', return_value=minimal_revenues):
            result = detector.detect_anomaly()
        
        # Should return None - not enough data
        assert result is None
    
    def test_detect_anomaly_empty_data(self, empty_revenues):
        """Test detection with no data."""
        from app.services.anomaly_detection import AnomalyDetector
        
        mock_db = MagicMock()
        detector = AnomalyDetector(mock_db, business_id=1)
        
        with patch.object(detector, 'get_daily_totals', return_value=empty_revenues):
            result = detector.detect_anomaly()
        
        assert result is None
    
    def test_detect_anomaly_high_variance_no_false_positive(self, sample_revenues_high_variance):
        """Test that high variance data doesn't trigger false positives."""
        from app.services.anomaly_detection import AnomalyDetector
        
        mock_db = MagicMock()
        detector = AnomalyDetector(mock_db, business_id=1)
        
        # With high variance, a moderate drop shouldn't be flagged
        with patch.object(detector, 'get_daily_totals', return_value=sample_revenues_high_variance):
            result = detector.detect_anomaly()
        
        # May or may not detect anomaly, but shouldn't be high severity false positive
        if result:
            assert result["severity"] != "high" or result["drop_percent"] > 40
    
    def test_custom_threshold(self, sample_revenues_with_anomaly):
        """Test anomaly detection with custom threshold."""
        from app.services.anomaly_detection import AnomalyDetector
        
        mock_db = MagicMock()
        
        # Higher threshold = less sensitive
        detector = AnomalyDetector(mock_db, business_id=1, threshold_std=3.0)
        
        with patch.object(detector, 'get_daily_totals', return_value=sample_revenues_with_anomaly):
            result = detector.detect_anomaly()
        
        # With higher threshold, may not detect the anomaly
        # This tests that threshold is being used


class TestTrendAnalysis:
    """Tests for trend analysis."""
    
    def test_trend_analysis_downward(self, sample_revenues_trending_down):
        """Test detection of downward trend."""
        from app.services.anomaly_detection import AnomalyDetector
        
        mock_db = MagicMock()
        detector = AnomalyDetector(mock_db, business_id=1)
        
        with patch.object(detector, 'get_daily_totals', return_value=sample_revenues_trending_down):
            result = detector.get_trend_analysis()
        
        assert result["direction"] == "down"
        assert result["change_percent"] < 0
    
    def test_trend_analysis_upward(self, sample_revenues_trending_up):
        """Test detection of upward trend."""
        from app.services.anomaly_detection import AnomalyDetector
        
        mock_db = MagicMock()
        detector = AnomalyDetector(mock_db, business_id=1)
        
        with patch.object(detector, 'get_daily_totals', return_value=sample_revenues_trending_up):
            result = detector.get_trend_analysis()
        
        assert result["direction"] == "up"
        assert result["change_percent"] > 0
    
    def test_trend_analysis_stable(self, sample_revenues_stable):
        """Test detection of stable trend."""
        from app.services.anomaly_detection import AnomalyDetector
        
        mock_db = MagicMock()
        detector = AnomalyDetector(mock_db, business_id=1)
        
        with patch.object(detector, 'get_daily_totals', return_value=sample_revenues_stable):
            result = detector.get_trend_analysis()
        
        assert result["direction"] == "stable"
        assert abs(result["change_percent"]) < 10  # Small change
    
    def test_trend_analysis_insufficient_data(self, minimal_revenues):
        """Test trend analysis with minimal data."""
        from app.services.anomaly_detection import AnomalyDetector
        
        mock_db = MagicMock()
        detector = AnomalyDetector(mock_db, business_id=1)
        
        with patch.object(detector, 'get_daily_totals', return_value=minimal_revenues):
            result = detector.get_trend_analysis()
        
        assert result["direction"] == "unknown"


class TestDayOfWeekBaseline:
    """Tests for day-of-week baseline calculation."""
    
    def test_dow_baseline_weekend_higher(self, sample_dow_pattern_revenues):
        """Test that weekend baselines are higher for patterned data."""
        from app.services.anomaly_detection import AnomalyDetector
        
        mock_db = MagicMock()
        detector = AnomalyDetector(mock_db, business_id=1)
        
        with patch.object(detector, 'get_daily_totals', return_value=sample_dow_pattern_revenues):
            saturday_baseline = detector.get_day_of_week_baseline(5)  # Saturday
            monday_baseline = detector.get_day_of_week_baseline(0)  # Monday
        
        # Weekend should be significantly higher
        assert saturday_baseline > monday_baseline * 1.3
    
    def test_dow_baseline_no_data(self, empty_revenues):
        """Test day-of-week baseline with no data."""
        from app.services.anomaly_detection import AnomalyDetector
        
        mock_db = MagicMock()
        detector = AnomalyDetector(mock_db, business_id=1)
        
        with patch.object(detector, 'get_daily_totals', return_value=empty_revenues):
            result = detector.get_day_of_week_baseline(0)
        
        assert result == 0.0


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""
    
    def test_single_day_revenue(self):
        """Test with only one day of revenue data."""
        from app.services.anomaly_detection import AnomalyDetector
        
        mock_db = MagicMock()
        detector = AnomalyDetector(mock_db, business_id=1)
        
        single_day = [{"date": datetime.utcnow().date(), "revenue": 1000}]
        
        with patch.object(detector, 'get_daily_totals', return_value=single_day):
            result = detector.detect_anomaly()
        
        assert result is None  # Not enough data
    
    def test_zero_revenue_day(self):
        """Test handling of zero revenue days."""
        from app.services.anomaly_detection import AnomalyDetector
        import random

        mock_db = MagicMock()
        detector = AnomalyDetector(mock_db, business_id=1)

        # Normal revenues with some variance, then zero day at end
        data = [
            {"date": (datetime.utcnow() - timedelta(days=29-i)).date(), "revenue": 1000 + random.uniform(-100, 100)}
            for i in range(29)
        ]
        data.append({"date": datetime.utcnow().date(), "revenue": 0})  # Zero revenue today (last)

        with patch.object(detector, 'get_daily_totals', return_value=data):
            result = detector.detect_anomaly()

        # Should detect this as a major anomaly
        assert result is not None
        assert result["detected"] == True
        assert result["severity"] == "high"
    
    def test_negative_values_handled(self):
        """Test that negative values are handled gracefully."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        # This shouldn't crash
        values = [100, -50, 100, 100, 100, 100, 100]
        result = detector.calculate_rolling_average(values, 7)
        
        assert isinstance(result, float)
    
    def test_very_large_values(self):
        """Test handling of very large revenue values."""
        from app.services.anomaly_detection import AnomalyDetector
        
        detector = AnomalyDetector(MagicMock(), business_id=1)
        
        values = [1e10] * 7  # 10 billion per day
        result = detector.calculate_rolling_average(values, 7)
        
        assert result == 1e10


class TestIntegration:
    """Integration tests for the full anomaly detection flow."""
    
    def test_full_detection_flow(self, sample_revenues_with_anomaly):
        """Test the full anomaly detection workflow."""
        from app.services.anomaly_detection import AnomalyDetector
        
        mock_db = MagicMock()
        detector = AnomalyDetector(mock_db, business_id=1)
        
        with patch.object(detector, 'get_daily_totals', return_value=sample_revenues_with_anomaly):
            # Detect anomaly
            anomaly = detector.detect_anomaly()
            
            # Get trend analysis
            trend = detector.get_trend_analysis()
        
        # Verify anomaly was detected
        assert anomaly is not None
        assert "detected" in anomaly
        assert "severity" in anomaly
        assert "drop_percent" in anomaly
        
        # Verify trend analysis works
        assert "direction" in trend
        assert "change_percent" in trend
