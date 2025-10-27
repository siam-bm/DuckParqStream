# Date-Range Partitioning Guide

## Overview

DuckParqStream now uses **intelligent date-range partitioning** for efficient data storage and querying.

### File Structure

```
data/parquet/
├── 2025/
│   ├── 09/
│   │   ├── log_01_20.parquet       (Sept 1-20 logs)
│   │   └── log_21_30.parquet       (Sept 21-30 logs)
│   └── 10/
│       ├── log_01_20.parquet       (Oct 1-20 logs)
│       ├── log_21_31.parquet       (Oct 21-31 logs)
│       ├── event_01_20.parquet     (Oct 1-20 events)
│       ├── event_21_31.parquet     (Oct 21-31 events)
│       └── transaction_01_20.parquet (Oct 1-20 transactions)
```

### Pattern

**Format:** `year/month/type_fromDay_toDay.parquet`

**Examples:**
- `2025/10/log_02_20.parquet` - Logs from October 2-20, 2025
- `2025/11/event_01_20.parquet` - Events from November 1-20, 2025
- `2024/12/transaction_21_31.parquet` - Transactions from December 21-31, 2024

---

## Benefits

### 1. **Easy File Discovery**
Know exactly which file contains your data:
- Need October 15 logs? → Look in `2025/10/log_01_20.parquet`
- Need November 25 events? → Look in `2025/11/event_21_31.parquet`

### 2. **Efficient Querying**
System automatically scans only relevant files:
- Query Oct 1-10? → Only reads `log_01_20.parquet`
- Query Oct 15-25? → Reads both `log_01_20.parquet` and `log_21_31.parquet`

### 3. **Type Separation**
Different data types in separate files:
- Logs, events, transactions don't mix
- Easier to manage and query
- Better compression per type

### 4. **Historical Data**
Insert old data anytime:
- Client sends data with date `2024-01-15`
- Goes to `2024/01/log_01_20.parquet`
- No conflicts with current data

---

## API Usage

### Ingest with Date and Type

**Endpoint:** `POST /ingest`

**Request Format:**
```json
{
  "records": [
    {"id": "123", "message": "test"}
  ],
  "data_date": "2025-10-15",
  "data_type": "log"
}
```

**Response:**
```json
{
  "status": "success",
  "records_processed": 1,
  "file": "2025/10/log_01_20.parquet",
  "file_size_mb": 0.02,
  "duration_seconds": 0.01
}
```

### Examples

#### Example 1: Insert Log Data
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {"id": "log001", "level": "ERROR", "message": "Database connection failed"}
    ],
    "data_date": "2025-10-15",
    "data_type": "log"
  }'
```

**Result:** Data stored in `2025/10/log_01_20.parquet`

#### Example 2: Insert Event Data
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {"id": "evt001", "user": "john", "action": "login"}
    ],
    "data_date": "2025-10-25",
    "data_type": "event"
  }'
```

**Result:** Data stored in `2025/10/event_21_31.parquet`

#### Example 3: Insert Old Data
```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "records": [
      {"id": "txn001", "amount": 99.99}
    ],
    "data_date": "2024-12-20",
    "data_type": "transaction"
  }'
```

**Result:** Data stored in `2024/12/transaction_01_20.parquet`

---

## Python Usage

### Import Engine
```python
from backend.ingestion import ingestion_engine
from datetime import datetime
```

### Insert with Date and Type
```python
# Insert log data for October 5
result = ingestion_engine.append_to_parquet(
    records=[
        {"id": "log001", "message": "App started"},
        {"id": "log002", "message": "User logged in"}
    ],
    data_date=datetime(2025, 10, 5),
    data_type="log"
)

print(result['file'])  # 2025/10/log_01_20.parquet
```

### Insert Current Data
```python
# If no date provided, uses current date
result = ingestion_engine.append_to_parquet(
    records=[{"id": "evt001", "action": "click"}],
    data_type="event"
)
```

### Insert Old Data
```python
# Insert data from last year
result = ingestion_engine.append_to_parquet(
    records=[{"id": "old001", "value": 123}],
    data_date=datetime(2024, 5, 10),
    data_type="legacy"
)

print(result['file'])  # 2024/05/legacy_01_20.parquet
```

---

## Querying

### Query All Data
```python
from backend.query_engine import query_engine

# Queries across all files
result = query_engine.execute_sql("""
    SELECT * FROM all_records
    WHERE data_type = 'log'
    LIMIT 100
""")
```

### Query by Date Range
```python
# System automatically finds relevant files
result = query_engine.query_by_date_range(
    "2025-10-01",
    "2025-10-31",
    limit=1000
)
```

### Query Specific Type
```python
# Filter by type
result = query_engine.execute_sql("""
    SELECT * FROM all_records
    WHERE data_type = 'event'
      AND data_date >= '2025-10-15'
    ORDER BY data_date DESC
""")
```

---

## Configuration

### Adjust Days Per File

Edit `backend/config.py`:

```python
# Each file contains 20 days by default
DAYS_PER_FILE = 20  # Change to 10, 15, 30, etc.
```

**Examples:**
- `DAYS_PER_FILE = 10` → More files, smaller size
  - `log_01_10.parquet`, `log_11_20.parquet`, `log_21_31.parquet`
- `DAYS_PER_FILE = 30` → Fewer files, larger size
  - `log_01_30.parquet`, `log_31_31.parquet`

### Default Data Type

```python
# Default type if not specified
TYPE_FIELD = 'data_type'  # Column name for type
```

---

## File Naming Rules

### Valid Type Names
- **Alphanumeric + underscore + hyphen**
- Lowercase automatically
- Invalid characters removed

**Examples:**
- `"Log Data"` → `logdata_01_20.parquet`
- `"user-events"` → `user-events_01_20.parquet`
- `"API_LOGS_v2"` → `api_logs_v2_01_20.parquet`

### Date Range Calculation

**Logic:**
- Days 1-20 → `01_20`
- Days 21-31 → `21_31` (or `21_28` for Feb, `21_30` for Apr, etc.)

**Examples:**
- Day 5 → File `01_20.parquet`
- Day 15 → File `01_20.parquet`
- Day 25 → File `21_31.parquet`
- Day 31 → File `21_31.parquet`

---

## Advanced Features

### 1. Concurrent Ingestion
Multiple clients can ingest to different date ranges simultaneously:

```python
# Thread 1: Current data
ingestion_engine.append_to_parquet(
    records=current_data,
    data_type="log"
)

# Thread 2: Historical data
ingestion_engine.append_to_parquet(
    records=historical_data,
    data_date=datetime(2024, 1, 1),
    data_type="log"
)
```

No conflicts! Different files.

### 2. Smart Query Optimization

System only loads necessary files:

```python
# Query Oct 5-10
# System loads: 2025/10/log_01_20.parquet only

# Query Oct 15-25
# System loads: 2025/10/log_01_20.parquet + 2025/10/log_21_31.parquet
```

### 3. Type-Based Filtering

Query specific types efficiently:

```python
# Only scans event files
query_engine._register_parquet_view(data_type="event")
result = query_engine.execute_sql("SELECT * FROM all_records")
```

---

## Migration from Old System

### Old Weekly Files
```
data_2025_w43.parquet  (Week 43 - mixed types)
data_2025_w44.parquet  (Week 44 - mixed types)
```

### New Date-Range Files
```
2025/10/log_01_20.parquet     (Oct 1-20 logs only)
2025/10/event_01_20.parquet   (Oct 1-20 events only)
2025/10/log_21_31.parquet     (Oct 21-31 logs only)
```

### Migration Steps

1. **Archive old files:**
```bash
mv data/parquet/*.parquet data/archive/
```

2. **Start using new system:**
```python
# All new data uses date + type
ingestion_engine.append_to_parquet(
    records=data,
    data_date=datetime(2025, 10, 27),
    data_type="log"
)
```

3. **Query both if needed:**
```python
# DuckDB can query old + new together
query = """
SELECT * FROM read_parquet([
    'data/archive/*.parquet',
    'data/parquet/**/*.parquet'
])
"""
```

---

## Testing

### Run Tests
```bash
python test_date_partitioning.py
```

**This will:**
1. Create test data for different dates
2. Verify file structure
3. Test querying
4. Show file organization

### Expected Output
```
📥 Test 1: Ingest log data for October 5, 2025
✅ Status: success
   File: 2025/10/log_01_20.parquet

📥 Test 2: Ingest event data for October 15, 2025
✅ Status: success
   File: 2025/10/event_01_20.parquet

📂 File Structure:
📁 2025/
  📁 10/
    📄 log_01_20.parquet (0.15 KB)
    📄 event_01_20.parquet (0.12 KB)
```

---

## Troubleshooting

### Files Not Created

**Check:**
1. Date format correct? Use `YYYY-MM-DD` or ISO format
2. Data directory writable?
3. Type name valid? (alphanumeric + underscore/hyphen)

### Can't Find Data

**Solutions:**
1. Check date: `SELECT DISTINCT data_date FROM all_records`
2. Check type: `SELECT DISTINCT data_type FROM all_records`
3. Verify file exists: `ls data/parquet/2025/10/`

### Query Slow

**Optimize:**
1. Specify date range to limit files scanned
2. Specify type to limit files scanned
3. Add indexes if needed (DuckDB automatic)

---

## Best Practices

### 1. Always Specify Type
```python
# Good
ingestion_engine.append_to_parquet(
    records=data,
    data_type="log"
)

# Avoid (uses "default")
ingestion_engine.append_to_parquet(records=data)
```

### 2. Use Meaningful Types
```python
# Good
data_type="api_logs"
data_type="user_events"
data_type="payment_transactions"

# Less helpful
data_type="data1"
data_type="stuff"
```

### 3. Query with Filters
```sql
-- Good (scans fewer files)
SELECT * FROM all_records
WHERE data_type = 'log'
  AND data_date >= '2025-10-01'
  AND data_date < '2025-11-01'

-- Less efficient (scans all files)
SELECT * FROM all_records
```

### 4. Monitor File Sizes
```python
# Check file stats
files = ingestion_engine.get_file_stats()
for file in files:
    print(f"{file['filename']}: {file['file_size_mb']} MB")
```

---

## Summary

✅ **Structure:** `year/month/type_fromDay_toDay.parquet`

✅ **Benefits:**
- Easy file discovery
- Efficient querying
- Type separation
- Historical data support

✅ **Usage:**
```python
ingestion_engine.append_to_parquet(
    records=[...],
    data_date=datetime(2025, 10, 15),
    data_type="log"
)
```

✅ **File Example:** `2025/10/log_01_20.parquet`

**Now you have intelligent, efficient, date-based partitioning! 🎉**
