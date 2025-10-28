"""
Test script for size-based partitioning
Verifies overflow logic, file renaming, and boundary cases
"""
import sys
import io
from pathlib import Path
from datetime import datetime
import shutil

# Set UTF-8 encoding for Windows console
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from ingestion import ingestion_engine
from config import MAX_ROWS_PER_FILE, DATA_DIR

def cleanup_test_data():
    """Remove test data before starting"""
    test_dirs = [
        DATA_DIR / "2025" / "09",
        DATA_DIR / "2025" / "10"
    ]
    for test_dir in test_dirs:
        if test_dir.exists():
            shutil.rmtree(test_dir)
    print("🧹 Cleaned up test data\n")

def print_file_structure():
    """Display current file structure"""
    print("\n📂 File Structure:")
    for year_dir in sorted(DATA_DIR.glob("*")):
        if year_dir.is_dir() and year_dir.name.isdigit():
            print(f"📁 {year_dir.name}/")
            for month_dir in sorted(year_dir.glob("*")):
                if month_dir.is_dir():
                    print(f"  📁 {month_dir.name}/")
                    for file in sorted(month_dir.glob("*.parquet")):
                        size_kb = file.stat().st_size / 1024
                        import pyarrow.parquet as pq
                        table = pq.read_table(file)
                        rows = table.num_rows
                        print(f"    📄 {file.name} ({rows} rows, {size_kb:.2f} KB)")

def test_1_initial_file_creation():
    """Test 1: Create initial file with 50 records"""
    print("=" * 60)
    print("Test 1: Initial File Creation (50 records)")
    print("=" * 60)

    records = [{"id": f"log_{i:03d}", "message": f"Test log message {i}"} for i in range(1, 51)]

    result = ingestion_engine.append_to_parquet(
        records=records,
        data_date=datetime(2025, 10, 5),
        data_type="log"
    )

    print(f"✅ Status: {result['status']}")
    print(f"📊 Records: {result['records_processed']}")
    print(f"📁 File: {result['file']}")
    print(f"💾 Size: {result['file_size_mb']} MB")

    expected_file = "log_05_31.parquet"
    assert expected_file in result['file'], f"Expected {expected_file}, got {result['file']}"
    print(f"✓ File created with expected name pattern")

    return result['file']

def test_2_append_within_limit():
    """Test 2: Append 30 more records (total 80, under limit)"""
    print("\n" + "=" * 60)
    print("Test 2: Append Within Limit (30 records, total 80)")
    print("=" * 60)

    records = [{"id": f"log_{i:03d}", "message": f"Test log message {i}"} for i in range(51, 81)]

    result = ingestion_engine.append_to_parquet(
        records=records,
        data_date=datetime(2025, 10, 8),
        data_type="log"
    )

    print(f"✅ Status: {result['status']}")
    print(f"📊 Records: {result['records_processed']}")
    print(f"📁 File: {result['file']}")

    expected_file = "log_05_31.parquet"
    assert expected_file in result['file'], f"Should still be in {expected_file}"
    print(f"✓ Records appended to existing file (under {MAX_ROWS_PER_FILE} limit)")

def test_3_overflow_trigger():
    """Test 3: Add 40 records to trigger overflow (total would be 120)"""
    print("\n" + "=" * 60)
    print(f"Test 3: Trigger Overflow (40 records, exceeds {MAX_ROWS_PER_FILE} limit)")
    print("=" * 60)

    records = [{"id": f"log_{i:03d}", "message": f"Test log message {i}"} for i in range(81, 121)]

    result = ingestion_engine.append_to_parquet(
        records=records,
        data_date=datetime(2025, 10, 12),
        data_type="log"
    )

    print(f"✅ Status: {result['status']}")
    print(f"📊 Records: {result['records_processed']}")
    print(f"📁 File: {result['file']}")

    # Should create new file starting from day 12
    expected_pattern = "log_12_31.parquet"
    assert expected_pattern in result['file'], f"Expected new file {expected_pattern}"
    print(f"✓ Overflow triggered: new file created from day 12")

    # Check that old file was renamed to actual range
    old_file = DATA_DIR / "2025" / "10" / "log_05_08.parquet"
    assert old_file.exists(), "Old file should be renamed to log_05_08.parquet"
    print(f"✓ Old file renamed to actual date range: log_05_08.parquet")

def test_4_multiple_types():
    """Test 4: Create different type in same month"""
    print("\n" + "=" * 60)
    print("Test 4: Multiple Types (event data)")
    print("=" * 60)

    records = [{"id": f"evt_{i:03d}", "action": f"user_action_{i}"} for i in range(1, 61)]

    result = ingestion_engine.append_to_parquet(
        records=records,
        data_date=datetime(2025, 10, 5),
        data_type="event"
    )

    print(f"✅ Status: {result['status']}")
    print(f"📊 Records: {result['records_processed']}")
    print(f"📁 File: {result['file']}")

    expected_file = "event_05_31.parquet"
    assert expected_file in result['file'], f"Expected {expected_file}"
    print(f"✓ Different type creates separate file")

def test_5_historical_data():
    """Test 5: Insert historical data (different month)"""
    print("\n" + "=" * 60)
    print("Test 5: Historical Data (September)")
    print("=" * 60)

    records = [{"id": f"log_{i:03d}", "message": f"Historical log {i}"} for i in range(1, 31)]

    result = ingestion_engine.append_to_parquet(
        records=records,
        data_date=datetime(2025, 9, 15),
        data_type="log"
    )

    print(f"✅ Status: {result['status']}")
    print(f"📊 Records: {result['records_processed']}")
    print(f"📁 File: {result['file']}")

    # Verify September file was created by checking directory
    sept_file = DATA_DIR / "2025" / "09" / result['file']
    assert sept_file.exists(), f"Should create file in September directory: {sept_file}"
    print(f"✓ Historical data stored in correct month directory")

def test_6_boundary_case_same_date():
    """Test 6: Verify same date can exist in multiple files"""
    print("\n" + "=" * 60)
    print("Test 6: Boundary Case (same date in multiple files)")
    print("=" * 60)

    # Check October log files
    oct_dir = DATA_DIR / "2025" / "10"
    log_files = sorted(oct_dir.glob("log_*.parquet"))

    if len(log_files) >= 2:
        import pyarrow.parquet as pq
        import pandas as pd

        # Read first file
        file1 = log_files[0]
        table1 = pq.read_table(file1)
        df1 = table1.to_pandas()
        max_date_file1 = pd.to_datetime(df1['data_date']).max()

        # Read second file
        file2 = log_files[1]
        table2 = pq.read_table(file2)
        df2 = table2.to_pandas()
        min_date_file2 = pd.to_datetime(df2['data_date']).min()

        print(f"📄 File 1: {file1.name}")
        print(f"   Last date: {max_date_file1.strftime('%Y-%m-%d')}")
        print(f"📄 File 2: {file2.name}")
        print(f"   First date: {min_date_file2.strftime('%Y-%m-%d')}")

        if max_date_file1 == min_date_file2:
            print(f"✓ Boundary case verified: {max_date_file1.strftime('%Y-%m-%d')} exists in both files")
        else:
            print(f"ℹ️ Files have sequential dates (no overlap)")
    else:
        print(f"ℹ️ Only one log file exists, boundary case not applicable yet")

def run_all_tests():
    """Run all tests sequentially"""
    print("\n" + "=" * 60)
    print("SIZE-BASED PARTITIONING TEST SUITE")
    print(f"MAX_ROWS_PER_FILE = {MAX_ROWS_PER_FILE}")
    print("=" * 60 + "\n")

    cleanup_test_data()

    try:
        test_1_initial_file_creation()
        test_2_append_within_limit()
        test_3_overflow_trigger()
        test_4_multiple_types()
        test_5_historical_data()
        test_6_boundary_case_same_date()

        print_file_structure()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60 + "\n")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        print_file_structure()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_all_tests()
