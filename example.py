"""
Complete Example: DuckParqStream Workflow
Demonstrates ingestion, querying, and analysis
"""
import sys
import io
from pathlib import Path

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Add backend to path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

from ingestion import ingestion_engine
from query_engine import query_engine
from test_data_generator import TestDataGenerator
import json
from datetime import datetime
import pandas as pd


def json_serial(obj):
    """JSON serializer for objects not serializable by default"""
    if isinstance(obj, (pd.Timestamp, datetime)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


def print_section(title):
    """Print formatted section header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def example_basic_ingestion():
    """Example 1: Basic JSON ingestion"""
    print_section("Example 1: Basic JSON Ingestion")

    # Sample records
    records = [
        {
            "id": "user_001",
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "age": 28,
            "country": "USA",
            "balance": 1250.50
        },
        {
            "id": "user_002",
            "name": "Bob Smith",
            "email": "bob@example.com",
            "age": 35,
            "country": "Canada",
            "balance": 3400.75
        },
        {
            "id": "user_003",
            "name": "Carol Williams",
            "email": "carol@example.com",
            "age": 42,
            "country": "UK",
            "balance": 5600.00
        }
    ]

    print(f"📥 Ingesting {len(records)} records...")
    result = ingestion_engine.append_to_parquet(records)

    print(f"\n✅ Result:")
    print(f"   Status: {result['status']}")
    print(f"   Records Processed: {result['records_processed']}")
    print(f"   File: {result['file']}")
    print(f"   Size: {result['file_size_mb']} MB")
    print(f"   Duration: {result['duration_seconds']}s")


def example_batch_generation():
    """Example 2: Generate and ingest large batch"""
    print_section("Example 2: Generate Large Dataset")

    generator = TestDataGenerator()

    # Generate 10,000 user records
    print("🔄 Generating 10,000 user records...")
    records = generator.generate_batch('user', count=10000)

    print("💾 Ingesting batch...")
    result = ingestion_engine.append_to_parquet(records)

    print(f"\n✅ Result:")
    print(f"   Records: {result['records_processed']:,}")
    print(f"   File Size: {result['file_size_mb']} MB")
    print(f"   Duration: {result['duration_seconds']}s")


def example_sql_queries():
    """Example 3: SQL queries"""
    print_section("Example 3: SQL Queries")

    # Query 1: Select all
    print("\n🔍 Query 1: First 5 records")
    result1 = query_engine.execute_sql(
        "SELECT * FROM all_records LIMIT 5"
    )
    print(f"   Found {result1['row_count']} records in {result1['duration_seconds']}s")
    if result1['data']:
        print(f"   Sample: {json.dumps(result1['data'][0], indent=2, default=json_serial)}")

    # Query 2: Count records
    print("\n🔍 Query 2: Total record count")
    result2 = query_engine.execute_sql(
        "SELECT COUNT(*) as total FROM all_records"
    )
    if result2['data']:
        print(f"   Total Records: {result2['data'][0]['total']:,}")

    # Query 3: Aggregation
    print("\n🔍 Query 3: Count by country")
    result3 = query_engine.execute_sql("""
        SELECT country, COUNT(*) as count
        FROM all_records
        WHERE country IS NOT NULL
        GROUP BY country
        ORDER BY count DESC
        LIMIT 5
    """)
    if result3['data']:
        print("   Top countries:")
        for row in result3['data']:
            print(f"     - {row['country']}: {row['count']:,} records")

    # Query 4: Average calculation
    print("\n🔍 Query 4: Average balance by country")
    result4 = query_engine.execute_sql("""
        SELECT
            country,
            ROUND(AVG(balance), 2) as avg_balance,
            COUNT(*) as user_count
        FROM all_records
        WHERE balance IS NOT NULL
          AND country IS NOT NULL
        GROUP BY country
        ORDER BY avg_balance DESC
        LIMIT 5
    """)
    if result4['data']:
        print("   Average balances:")
        for row in result4['data']:
            print(f"     - {row['country']}: ${row['avg_balance']} ({row['user_count']} users)")


def example_search_and_filter():
    """Example 4: Search and filtering"""
    print_section("Example 4: Search and Filter")

    # Search by ID
    print("\n🔍 Search by ID: user_001")
    result1 = query_engine.query_by_id("user_001")
    if result1['row_count'] > 0:
        print(f"   Found: {json.dumps(result1['data'][0], indent=2, default=json_serial)}")
    else:
        print("   Record not found")

    # Search by text
    print("\n🔍 Full-text search: 'alice'")
    result2 = query_engine.search("alice", limit=5)
    print(f"   Found {result2['row_count']} matching records")

    # Filter by date
    print("\n🔍 Recent records (last 24 hours)")
    result3 = query_engine.query_recent(hours=24, limit=5)
    print(f"   Found {result3['row_count']} recent records")


def example_statistics():
    """Example 5: Dataset statistics"""
    print_section("Example 5: Dataset Statistics")

    # Get comprehensive stats
    stats = query_engine.get_statistics()

    if stats['status'] == 'success':
        stat_data = stats['statistics']

        print(f"\n📊 Overall Statistics:")
        print(f"   Total Records: {stat_data.get('total_records', 0):,}")

        if stat_data.get('date_range'):
            dr = stat_data['date_range']
            print(f"   Date Range: {dr['earliest']} to {dr['latest']}")

        if stat_data.get('weekly_distribution'):
            print(f"\n📅 Weekly Distribution:")
            for week_data in stat_data['weekly_distribution'][:5]:
                print(f"     - {week_data['week']}: {week_data['count']:,} records")

        if stat_data.get('schema'):
            print(f"\n📋 Schema ({len(stat_data['schema'])} columns):")
            for col in stat_data['schema'][:10]:
                print(f"     - {col['column_name']}: {col['column_type']}")

    # File statistics
    print("\n📁 File Statistics:")
    files = ingestion_engine.get_file_stats()
    total_size = 0
    total_rows = 0

    for file_info in files:
        print(f"   - {file_info['filename']}:")
        print(f"       Rows: {file_info['row_count']:,}")
        print(f"       Size: {file_info['file_size_mb']:.2f} MB")
        total_size += file_info['file_size_mb']
        total_rows += file_info['row_count']

    print(f"\n   Total Files: {len(files)}")
    print(f"   Total Rows: {total_rows:,}")
    print(f"   Total Size: {total_size:.2f} MB")


def example_advanced_analytics():
    """Example 6: Advanced analytics"""
    print_section("Example 6: Advanced Analytics")

    # Percentile analysis
    print("\n📊 Balance distribution (percentiles)")
    result = query_engine.execute_sql("""
        SELECT
            ROUND(MIN(balance), 2) as min,
            ROUND(percentile_cont(0.25) WITHIN GROUP (ORDER BY balance), 2) as p25,
            ROUND(percentile_cont(0.50) WITHIN GROUP (ORDER BY balance), 2) as median,
            ROUND(percentile_cont(0.75) WITHIN GROUP (ORDER BY balance), 2) as p75,
            ROUND(MAX(balance), 2) as max
        FROM all_records
        WHERE balance IS NOT NULL
    """)

    if result['data']:
        stats = result['data'][0]
        print(f"   Min:    ${stats['min']}")
        print(f"   P25:    ${stats['p25']}")
        print(f"   Median: ${stats['median']}")
        print(f"   P75:    ${stats['p75']}")
        print(f"   Max:    ${stats['max']}")

    # Time-based analysis
    print("\n📈 Records by hour of day")
    result2 = query_engine.execute_sql("""
        SELECT
            EXTRACT(HOUR FROM ingested_at) as hour,
            COUNT(*) as count
        FROM all_records
        GROUP BY hour
        ORDER BY hour
    """)

    if result2['data'] and len(result2['data']) > 0:
        print("   Hourly distribution:")
        for row in result2['data'][:5]:
            print(f"     - Hour {int(row['hour']):02d}:00: {row['count']:,} records")


def run_all_examples():
    """Run all examples in sequence"""
    print("\n" + "=" * 60)
    print("  🦆 DuckParqStream - Complete Examples")
    print("=" * 60)

    try:
        # Run examples
        example_basic_ingestion()
        example_batch_generation()
        example_sql_queries()
        example_search_and_filter()
        example_statistics()
        example_advanced_analytics()

        # Final summary
        print_section("✅ All Examples Completed!")
        print("\n🎉 You now have a working local JSON database with:")
        print("   • Ingested test data")
        print("   • Executed various queries")
        print("   • Analyzed statistics")
        print("   • Performed advanced analytics")
        print("\n📚 Next steps:")
        print("   • Start the web UI: python run.py")
        print("   • Read the docs: README.md")
        print("   • Try your own data!")

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\n💡 Make sure you've installed dependencies:")
        print("   pip install -r requirements.txt")
        raise


if __name__ == '__main__':
    run_all_examples()
