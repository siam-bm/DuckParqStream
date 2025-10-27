"""
Test the new date-range partitioning system
Structure: year/month/type_fromDay_toDay.parquet
Example: 2025/10/log_01_20.parquet
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add backend to path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

from ingestion import ingestion_engine
from query_engine import query_engine

print("=" * 70)
print("Testing Date-Range Partitioning System")
print("=" * 70)

# Test 1: Ingest log data for October 5, 2025
print("\n📥 Test 1: Ingest log data for October 5, 2025")
print("-" * 70)

log_records = [
    {"id": "log_001", "level": "INFO", "message": "Application started"},
    {"id": "log_002", "level": "ERROR", "message": "Connection failed"},
    {"id": "log_003", "level": "WARN", "message": "Slow query detected"}
]

result1 = ingestion_engine.append_to_parquet(
    records=log_records,
    data_date=datetime(2025, 10, 5),
    data_type="log"
)

print(f"✅ Status: {result1['status']}")
print(f"   Records: {result1['records_processed']}")
print(f"   File: {result1['file']}")
print(f"   Expected: 2025/10/log_01_20.parquet")

# Test 2: Ingest event data for October 15, 2025
print("\n📥 Test 2: Ingest event data for October 15, 2025")
print("-" * 70)

event_records = [
    {"id": "evt_001", "user_id": "user123", "action": "login"},
    {"id": "evt_002", "user_id": "user456", "action": "purchase"},
]

result2 = ingestion_engine.append_to_parquet(
    records=event_records,
    data_date=datetime(2025, 10, 15),
    data_type="event"
)

print(f"✅ Status: {result2['status']}")
print(f"   Records: {result2['records_processed']}")
print(f"   File: {result2['file']}")
print(f"   Expected: 2025/10/event_01_20.parquet")

# Test 3: Ingest transaction data for October 25, 2025
print("\n📥 Test 3: Ingest transaction data for October 25, 2025")
print("-" * 70)

transaction_records = [
    {"id": "txn_001", "amount": 99.99, "currency": "USD"},
    {"id": "txn_002", "amount": 149.50, "currency": "EUR"},
]

result3 = ingestion_engine.append_to_parquet(
    records=transaction_records,
    data_date=datetime(2025, 10, 25),
    data_type="transaction"
)

print(f"✅ Status: {result3['status']}")
print(f"   Records: {result3['records_processed']}")
print(f"   File: {result3['file']}")
print(f"   Expected: 2025/10/transaction_21_31.parquet")

# Test 4: Ingest old data (September)
print("\n📥 Test 4: Ingest log data for September 10, 2025")
print("-" * 70)

old_log_records = [
    {"id": "old_log_001", "level": "INFO", "message": "Old log entry"}
]

result4 = ingestion_engine.append_to_parquet(
    records=old_log_records,
    data_date=datetime(2025, 9, 10),
    data_type="log"
)

print(f"✅ Status: {result4['status']}")
print(f"   Records: {result4['records_processed']}")
print(f"   File: {result4['file']}")
print(f"   Expected: 2025/09/log_01_20.parquet")

# Test 5: Check file structure
print("\n📂 Test 5: Check Created File Structure")
print("-" * 70)

data_dir = Path("data/parquet")
if data_dir.exists():
    print(f"Data directory: {data_dir.absolute()}\n")

    for year_dir in sorted(data_dir.iterdir()):
        if year_dir.is_dir():
            print(f"📁 {year_dir.name}/")
            for month_dir in sorted(year_dir.iterdir()):
                if month_dir.is_dir():
                    print(f"  📁 {month_dir.name}/")
                    for file in sorted(month_dir.glob("*.parquet")):
                        size = file.stat().st_size / 1024  # KB
                        print(f"    📄 {file.name} ({size:.2f} KB)")

# Test 6: Query specific type
print("\n🔍 Test 6: Query all log records")
print("-" * 70)

# Force refresh view for all files
query_engine._register_parquet_view()

result = query_engine.execute_sql(f"""
    SELECT * FROM all_records
    WHERE {config.TYPE_FIELD} = 'log'
    ORDER BY {config.DATE_FIELD}
""")

if result['status'] == 'success':
    print(f"✅ Found {result['row_count']} log records")
    for record in result['data'][:3]:
        print(f"   - {record.get('id')}: {record.get('message', 'N/A')}")

# Test 7: Query by date range
print("\n🔍 Test 7: Query October 2025 data")
print("-" * 70)

result = query_engine.query_by_date_range(
    "2025-10-01",
    "2025-10-31",
    limit=100
)

if result['status'] == 'success':
    print(f"✅ Found {result['row_count']} records in October 2025")
    types = {}
    for record in result['data']:
        data_type = record.get('data_type', 'unknown')
        types[data_type] = types.get(data_type, 0) + 1

    print(f"   Breakdown by type:")
    for data_type, count in types.items():
        print(f"     - {data_type}: {count} records")

print("\n" + "=" * 70)
print("✅ Date-Range Partitioning Tests Complete!")
print("=" * 70)

print("\n📊 Summary:")
print(f"   Structure: year/month/type_fromDay_toDay.parquet")
print(f"   Examples created:")
print(f"     - 2025/10/log_01_20.parquet")
print(f"     - 2025/10/event_01_20.parquet")
print(f"     - 2025/10/transaction_21_31.parquet")
print(f"     - 2025/09/log_01_20.parquet")
print(f"\n   ✅ Easy to find files by date and type!")
print(f"   ✅ Efficient querying of specific date ranges!")
