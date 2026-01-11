# CSV Upload Format Specification

## Overview

Procoagent accepts transaction data via CSV file upload. This document specifies the required format for successful data ingestion.

## File Requirements

- **Format:** CSV (Comma-Separated Values)
- **Encoding:** UTF-8
- **Max file size:** 10 MB
- **Max rows per upload:** 10,000

## Required Columns

| Column Name | Type | Required | Description |
|-------------|------|----------|-------------|
| `timestamp` | ISO 8601 datetime | Yes | When the transaction occurred |
| `amount` | Decimal | Yes | Transaction amount (positive number) |
| `description` | String | Yes | Service or item description |

## Optional Columns

| Column Name | Type | Default | Description |
|-------------|------|---------|-------------|
| `transaction_id` | String | Auto-generated | Unique identifier for the transaction |
| `customer_id` | String | null | Customer identifier for segmentation |
| `payment_method` | String | null | Payment type (card, cash, etc.) |

## Example CSV
```csv
transaction_id,timestamp,amount,description,customer_id,payment_method
TXN_001,2026-01-10T10:30:00,50.00,Haircut,CUST_001,card
TXN_002,2026-01-10T11:00:00,75.00,Color Treatment,CUST_002,card
TXN_003,2026-01-10T14:30:00,25.00,Blowout,CUST_001,cash
TXN_004,2026-01-10T15:45:00,120.00,Highlights,CUST_003,card
```

## Timestamp Formats

The following timestamp formats are accepted:

| Format | Example |
|--------|---------|
| ISO 8601 (preferred) | `2026-01-10T10:30:00` |
| ISO 8601 with timezone | `2026-01-10T10:30:00-05:00` |
| Date only | `2026-01-10` (time defaults to 00:00:00) |
| US format | `01/10/2026 10:30 AM` |

## Amount Rules

- Must be a positive decimal number
- Up to 2 decimal places
- No currency symbols (e.g., use `50.00` not `$50.00`)
- Use period (.) as decimal separator

## Validation & Error Handling

### Validation Process

1. File type verification (must be `.csv`)
2. Header row validation (required columns present)
3. Row-by-row data validation
4. Duplicate transaction_id detection

### Error Behavior

- **Invalid file type:** Upload rejected entirely
- **Missing required columns:** Upload rejected with column list
- **Invalid row data:** Row skipped, others imported
- **Duplicate transaction_id:** Row skipped (existing data preserved)

### Response Format
```json
{
  "imported_count": 47,
  "skipped_count": 3,
  "errors": [
    {
      "row": 12,
      "field": "amount",
      "message": "Invalid number format: 'fifty'"
    },
    {
      "row": 25,
      "field": "timestamp",
      "message": "Could not parse date: '13/45/2026'"
    }
  ]
}
```

## Best Practices

1. **Export from your POS system** - Most POS systems can export to CSV
2. **Verify encoding** - Save as UTF-8 to avoid character issues
3. **Include headers** - First row must be column names
4. **Consistent timestamps** - Use the same format throughout
5. **Review before upload** - Check a few rows for formatting issues

## Sample Files

Download sample CSV files for testing:

- [salon_transactions_sample.csv](../backend/sample_data/salon_transactions_normal.csv)
- [restaurant_transactions_sample.csv](../backend/sample_data/restaurant_transactions_normal.csv)
- [minimal_test.csv](../backend/sample_data/minimal_test.csv)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Missing required columns" | Check column names match exactly (case-sensitive) |
| "Invalid timestamp" | Use ISO 8601 format: `YYYY-MM-DDTHH:MM:SS` |
| "Invalid amount" | Remove currency symbols, use period for decimal |
| "File too large" | Split into multiple files under 10MB |
| "Encoding error" | Re-save file as UTF-8 in your spreadsheet app |
