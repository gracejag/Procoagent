#!/usr/bin/env python3
"""
Sample Data Generator for Procoagent
Generates realistic transaction data for testing
"""

import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
NUM_TRANSACTIONS = 200
OUTPUT_DIR = Path(__file__).parent.parent / "sample_data"
BUSINESS_TYPES = {
    "salon": {
        "services": ["Haircut", "Color", "Highlights", "Blowout", "Treatment", "Extensions"],
        "price_range": (25, 250),
        "peak_days": [4, 5],  # Friday, Saturday
    },
    "fitness": {
        "services": ["Monthly Membership", "Personal Training", "Class Drop-in", "Day Pass", "Merchandise"],
        "price_range": (15, 150),
        "peak_days": [0, 1, 2],  # Mon, Tue, Wed
    },
    "restaurant": {
        "services": ["Dine-in", "Takeout", "Delivery", "Catering", "Gift Card"],
        "price_range": (12, 85),
        "peak_days": [4, 5, 6],  # Fri, Sat, Sun
    },
    "cafe": {
        "services": ["Coffee", "Espresso Drinks", "Pastries", "Breakfast", "Lunch", "Merchandise"],
        "price_range": (4, 25),
        "peak_days": [0, 1, 2, 3, 4],  # Weekdays
    },
}


def generate_transactions(
    business_type: str = "salon",
    num_transactions: int = NUM_TRANSACTIONS,
    start_date: datetime = None,
    include_anomaly: bool = True,
) -> list[dict]:
    """Generate realistic transaction data."""
    
    if start_date is None:
        start_date = datetime.now() - timedelta(days=30)
    
    config = BUSINESS_TYPES.get(business_type, BUSINESS_TYPES["salon"])
    transactions = []
    
    # Generate customer IDs (some repeat customers)
    num_customers = num_transactions // 3
    customer_ids = [f"CUST_{i:04d}" for i in range(1, num_customers + 1)]
    
    for i in range(num_transactions):
        # Distribute transactions across the date range
        days_offset = random.randint(0, 30)
        hours_offset = random.randint(9, 20)  # Business hours
        minutes_offset = random.randint(0, 59)
        
        transaction_date = start_date + timedelta(
            days=days_offset, 
            hours=hours_offset, 
            minutes=minutes_offset
        )
        
        # Adjust amount based on day of week (higher on peak days)
        base_min, base_max = config["price_range"]
        if transaction_date.weekday() in config["peak_days"]:
            amount = round(random.uniform(base_min * 1.2, base_max * 1.3), 2)
        else:
            amount = round(random.uniform(base_min, base_max), 2)
        
        # Simulate anomaly: revenue drop in the middle of the period
        if include_anomaly and 12 <= days_offset <= 15:
            if random.random() < 0.6:  # 60% chance to skip transaction
                continue
            amount *= 0.5  # Reduce amount for remaining transactions
        
        transaction = {
            "transaction_id": f"TXN_{i:06d}",
            "timestamp": transaction_date.isoformat(),
            "amount": round(amount, 2),
            "description": random.choice(config["services"]),
            "customer_id": random.choice(customer_ids),
            "payment_method": random.choice(["card", "cash", "card", "card"]),  # Weighted toward card
        }
        transactions.append(transaction)
    
    # Sort by timestamp
    transactions.sort(key=lambda x: x["timestamp"])
    return transactions


def save_to_csv(transactions: list[dict], filename: str) -> Path:
    """Save transactions to CSV file."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    filepath = OUTPUT_DIR / filename
    
    if not transactions:
        print(f"Warning: No transactions to save")
        return filepath
    
    fieldnames = ["transaction_id", "timestamp", "amount", "description", "customer_id", "payment_method"]
    
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)
    
    print(f"Saved {len(transactions)} transactions to {filepath}")
    return filepath


def main():
    """Generate sample data files for all business types."""
    print("Generating sample transaction data...\n")
    
    for business_type in BUSINESS_TYPES.keys():
        # Normal data (no anomaly)
        transactions = generate_transactions(
            business_type=business_type,
            include_anomaly=False,
        )
        save_to_csv(transactions, f"{business_type}_transactions_normal.csv")
        
        # Data with anomaly (for testing detection)
        transactions_anomaly = generate_transactions(
            business_type=business_type,
            include_anomaly=True,
        )
        save_to_csv(transactions_anomaly, f"{business_type}_transactions_anomaly.csv")
    
    # Generate a minimal test file
    minimal = generate_transactions(num_transactions=10, include_anomaly=False)
    save_to_csv(minimal, "minimal_test.csv")
    
    print("\n✅ Sample data generation complete!")
    print(f"Files saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
