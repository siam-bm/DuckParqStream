# Size-Based Partitioning Guide

## Overview

DuckParqStream uses **intelligent size-based partitioning** where files are created based on row count limits, ensuring optimal file sizes and easy date-based discovery.

### How It Works

Instead of fixed date ranges, files grow until they reach `MAX_ROWS_PER_FILE` limit, then a new file is created starting from the overflow date.

---

## File Creation Logic

### Example Scenario

**Configuration:** `MAX_ROWS_PER_FILE = 100`

#### Day 1-5: Initial File
```
Client sends 100 log records spanning Oct 1-5
→ Creates: 2025/10/log_01_30.parquet (100 rows, dates: Oct 1-5)
```

#### Day 5: Overflow
```
Client sends 50 more log records for Oct 5
→ File full (100 rows)
→ Renames: log_01_30.parquet → log_01_05.parquet (actual date range)
→ Creates: 2025/10/log_05_30.parquet (50 new rows starting from Oct 5)
```

#### Day 8: Continue
```
Client sends 30 log records for Oct 8
→ Appends to: 2025/10/log_05_30.parquet (now 80 rows)
```

#### Day 12: Another Overflow
```
Client sends 40 log records for Oct 12
→ File full (100 rows)
→ Renames: log_05_30.parquet → log_05_12.parquet (actual date range)
→ Creates: 2025/10/log_12_30.parquet (40 new rows)
```

### Final Structure
```
data/parquet/2025/10/
├── log_01_05.parquet  (100 rows: Oct 1-5)
├── log_05_12.parquet  (100 rows: Oct 5-12)
└── log_12_30.parquet  (40 rows: Oct 12+)
```

---

## Key Features

### 1. **Size-Controlled Files**
- Each file contains max `MAX_ROWS_PER_FILE` rows
- Prevents files from growing too large
- Consistent file sizes for better performance

### 2. **Sequential Date Ranges**
- Files named by actual date range: `type_fromDay_toDay.parquet`
- Easy to find data by date
- No gaps or overlaps

### 3. **Automatic File Management**
- System automatically finds right file for date
- Renames files to actual date range when full
- Creates new files when needed

### 4. **Boundary Handling**
- Same date can span multiple files (normal behavior)
- Example: Oct 5 data in both `log_01_05.parquet` and `log_05_12.parquet`
- Query system handles this automatically

---

## Configuration

### Set Row Limit

Edit `backend/config.py`:

```python
# Maximum rows per file before creating new file
MAX_ROWS_PER_FILE = 100  # Adjust based on needs

# Examples:
# MAX_ROWS_PER_FILE = 50   → Smaller files, more files
# MAX_ROWS_PER_FILE = 500  → Larger files, fewer files
# MAX_ROWS_PER_FILE = 1000 → For high-volume data
```

### Recommended Settings

| Data Volume | Rows/File | File Size | Files/Month |
|-------------|-----------|-----------|-------------|
| Low         | 100       | ~1 MB     | 1-5         |
| Medium      | 500       | ~5 MB     | 3-10        |
| High        | 1000      | ~10 MB    | 5-20        |
| Very High   | 5000      | ~50 MB    | 10-50       |

---

## Examples

### Example 1: Sequential Ingestion

```python
from backend.ingestion import ingestion_engine
from datetime import datetime

# Day 1: 40 records
result = ingestion_engine.append_to_parquet(
    records=[...],  # 40 records
    data_date=datetime(2025, 10, 1),
    data_type="log"
)
# Creates: log_01_30.parquet (40 rows)

# Day 2: 30 records
result = ingestion_engine.append_to_parquet(
    records=[...],  # 30 records
    data_date=datetime(2025, 10, 2),
    data_type="log"
)
# Appends to: log_01_30.parquet (70 rows)

# Day 3: 50 records (overflow!)
result = ingestion_engine.append_to_parquet(
    records=[...],  # 50 records
    data_date=datetime(2025, 10, 3),
    data_type="log"
)
# Renames: log_01_30.parquet → log_01_02.parquet (100 rows)
# Creates: log_03_30.parquet (20 rows)
```

### Example 2: Out-of-Order Dates

```python
# Client sends old data
result = ingestion_engine.append_to_parquet(
    records=[...],  # 20 records
    data_date=datetime(2025, 9, 15),
    data_type="log"
)
# Creates: 2025/09/log_15_30.parquet (20 rows)

# Then sends current data
result = ingestion_engine.append_to_parquet(
    records=[...],  # 30 records
    data_date=datetime(2025, 10, 5),
    data_type="log"
)
# Appends to existing file or creates new one
```

### Example 3: Multiple Types

```python
# Logs
result = ingestion_engine.append_to_parquet(
    records=[...],  # 80 records
    data_date=datetime(2025, 10, 5),
    data_type="log"
)
# Creates: log_05_30.parquet (80 rows)

# Events (separate file)
result = ingestion_engine.append_to_parquet(
    records=[...],  # 60 records
    data_date=datetime(2025, 10, 5),
    data_type="event"
)
# Creates: event_05_30.parquet (60 rows)

# Same date, different files by type!
```

---

## Querying

### Query by Date

The system automatically finds all relevant files:

```python
from backend.query_engine import query_engine

# Query Oct 5 data
result = query_engine.query_by_date_range(
    "2025-10-05",
    "2025-10-05",
    limit=1000
)
# Scans: log_01_05.parquet + log_05_12.parquet (if date spans both)
```

### Query by Type

```python
# All logs
result = query_engine.execute_sql("""
    SELECT * FROM all_records
    WHERE data_type = 'log'
    ORDER BY data_date
""")
```

### Query Specific Range

```python
# Oct 1-10
result = query_engine.query_by_date_range(
    "2025-10-01",
    "2025-10-10",
    limit=5000
)
# System determines which files to scan based on date ranges in filenames
```

---

## File Naming

### Pattern

```
type_fromDay_toDay.parquet
```

**Components:**
- `type`: Data type (log, event, etc.)
- `fromDay`: First day in file (01-31)
- `toDay`: Last day in file (01-31)

### Examples

```
log_01_05.parquet      → Logs from Oct 1-5
log_05_12.parquet      → Logs from Oct 5-12 (overflow from previous)
event_08_15.parquet    → Events from Oct 8-15
transaction_20_30.parquet → Transactions from Oct 20-30
```

### Dynamic Naming

Files start with optimistic end date (`_30`) and get renamed to actual range when full:

```
Initial:  log_01_30.parquet
After 100 rows on day 5:
Renamed:  log_01_05.parquet
New:      log_05_30.parquet
```

---

## Advantages

### 1. **Predictable File Sizes**
- Each file ≈ MAX_ROWS_PER_FILE rows
- No huge files that slow down queries
- No tiny files that waste space

### 2. **Easy Date Discovery**
```
Need Oct 5 data?
→ Look for files with range covering day 5
→ log_01_05.parquet ✓
→ log_05_12.parquet ✓
```

### 3. **Automatic Optimization**
- System handles file creation
- System handles renaming
- System handles overflow

### 4. **Type Isolation**
```
2025/10/
├── log_01_05.parquet      (logs only)
├── event_01_08.parquet    (events only)
└── transaction_05_15.parquet (transactions only)
```

---

## Edge Cases

### Same Date in Multiple Files

**Normal behavior** - happens at overflow:

```
Day 5 data in:
- log_01_05.parquet (first 80 records)
- log_05_12.parquet (next 40 records from same day)
```

**Query handles automatically:**
```sql
SELECT * FROM all_records WHERE data_date = '2025-10-05'
-- Returns all 120 records from both files
```

### File Rename Race Condition

System uses atomic operations:
1. Read current file
2. Check row count
3. If full:
   - Create new file first
   - Then rename old file
4. Prevents data loss

### Month Boundaries

Files respect month boundaries:

```
Sept data:  2025/09/log_25_30.parquet
Oct data:   2025/10/log_01_08.parquet
(Separate months = separate directories)
```

---

## Monitoring

### Check File Sizes

```python
from backend.ingestion import ingestion_engine

files = ingestion_engine.get_file_stats()
for file in files:
    print(f"{file['filename']}: {file['row_count']} rows, {file['file_size_mb']} MB")
```

### Find Files Approaching Limit

```python
files = ingestion_engine.get_file_stats()
for file in files:
    if file['row_count'] > MAX_ROWS_PER_FILE * 0.9:  # 90% full
        print(f"⚠️ {file['filename']} nearly full: {file['row_count']} rows")
```

---

## Best Practices

### 1. **Set Appropriate Limit**
```python
# Low volume (few records/day)
MAX_ROWS_PER_FILE = 100

# Medium volume (thousands/day)
MAX_ROWS_PER_FILE = 1000

# High volume (millions/day)
MAX_ROWS_PER_FILE = 10000
```

### 2. **Monitor File Growth**
Check file stats regularly to ensure limits are appropriate

### 3. **Use Meaningful Types**
```python
data_type = "api_logs"      # Good
data_type = "user_events"   # Good
data_type = "data"          # Less helpful
```

### 4. **Query with Filters**
```sql
-- Efficient (uses file date ranges)
WHERE data_date >= '2025-10-01' AND data_date < '2025-10-08'

-- Less efficient (scans all files)
WHERE value > 100
```

---

## Comparison with Fixed Date Ranges

### Old System (Fixed Ranges)
```
log_01_20.parquet  → Always days 1-20, any size
log_21_31.parquet  → Always days 21-31, any size
```

**Problems:**
- Files could be 1 KB or 1 GB
- Unpredictable sizes
- Some files huge, some tiny

### New System (Size-Based)
```
log_01_05.parquet  → Exactly 100 rows, days 1-5
log_05_12.parquet  → Exactly 100 rows, days 5-12
```

**Benefits:**
- Predictable file sizes
- Optimal for querying
- Easy to manage

---

## Summary

✅ **Size-controlled** - Files limited to MAX_ROWS_PER_FILE

✅ **Auto-managed** - System handles overflow and renaming

✅ **Date-sequential** - Files named by actual date range

✅ **Easy discovery** - Filename tells you what's inside

✅ **Boundary safe** - Handles same date across files

✅ **Type-separated** - Different types in different files

**Configuration:**
```python
MAX_ROWS_PER_FILE = 100  # Adjust to your needs
```

**Example Structure:**
```
2025/10/
├── log_01_05.parquet     (100 rows, Oct 1-5)
├── log_05_12.parquet     (100 rows, Oct 5-12)
├── event_01_08.parquet   (100 rows, Oct 1-8)
└── event_08_30.parquet   (75 rows, Oct 8+)
```

**Your data is now organized by size and date for optimal performance! 🚀**
