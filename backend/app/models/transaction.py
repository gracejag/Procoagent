from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey
from datetime import datetime

from ..database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    amount = Column(Float, nullable=False)
    description = Column(String)
    transaction_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)