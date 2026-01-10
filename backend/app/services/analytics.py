from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from ..models.transaction import Transaction


def get_daily_revenue(db: Session, business_id: int, days: int = 30):
    """Get daily revenue totals for the past N days."""
    start = datetime.utcnow() - timedelta(days=days)
    
    return db.query(
        func.date(Transaction.transaction_date).label('date'),
        func.sum(Transaction.amount).label('revenue'),
        func.count(Transaction.id).label('transaction_count')
    ).filter(
        Transaction.business_id == business_id,
        Transaction.transaction_date >= start
    ).group_by(
        func.date(Transaction.transaction_date)
    ).order_by(
        func.date(Transaction.transaction_date)
    ).all()


def get_revenue_summary(db: Session, business_id: int):
    """Get revenue summary: today, this week, this month."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=now.weekday())
    month_start = today_start.replace(day=1)
    
    def get_total(start_date):
        result = db.query(func.sum(Transaction.amount)).filter(
            Transaction.business_id == business_id,
            Transaction.transaction_date >= start_date
        ).scalar()
        return result or 0.0
    
    return {
        "today": get_total(today_start),
        "this_week": get_total(week_start),
        "this_month": get_total(month_start)
    }
