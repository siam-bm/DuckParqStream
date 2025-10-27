"""
Debug search functionality directly (no API)
"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

# Import after path is set
import traceback

try:
    from query_engine import DuckDBQueryEngine
    from config import DATA_DIR, DUCKDB_FILE

    print("Creating query engine...")
    engine = DuckDBQueryEngine()

    print("\n" + "=" * 60)
    print("Testing search with column=None")
    print("=" * 60)

    result = engine.search('siam', column=None, limit=100)

    print(f"\nResult status: {result['status']}")

    if result['status'] == 'error':
        print(f"Error message: {result.get('message', 'Unknown')}")
    else:
        print(f"Success! Found {result['row_count']} records")
        print(f"Query: {result['query']}")

except Exception as e:
    print(f"\n❌ ERROR: {type(e).__name__}")
    print(f"Message: {e}")
    print("\nFull traceback:")
    traceback.print_exc()
