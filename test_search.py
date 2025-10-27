"""
Test search functionality
Run this when the API server is NOT running
"""
import sys
from pathlib import Path

# Add backend to path
backend_dir = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_dir))

from query_engine import query_engine
import json

print("=" * 60)
print("Testing Search Functionality")
print("=" * 60)

# Test 1: Search with column=None (search all columns)
print("\nTest 1: Search with column=None")
print("-" * 60)
result1 = query_engine.search('siam', column=None, limit=10)
print(f"Status: {result1['status']}")
if result1['status'] == 'success':
    print(f"Found {result1['row_count']} records")
    print(f"Query: {result1['query']}")
    print(f"Duration: {result1['duration_seconds']}s")
    if result1['data']:
        print(f"\nFirst result:")
        print(json.dumps(result1['data'][0], indent=2, default=str))
else:
    print(f"Error: {result1.get('message', 'Unknown error')}")

# Test 2: Search with specific column
print("\n" + "=" * 60)
print("Test 2: Search in 'name' column")
print("-" * 60)
result2 = query_engine.search('alice', column='name', limit=10)
print(f"Status: {result2['status']}")
if result2['status'] == 'success':
    print(f"Found {result2['row_count']} records")
    print(f"Query: {result2['query']}")
    print(f"Duration: {result2['duration_seconds']}s")
else:
    print(f"Error: {result2.get('message', 'Unknown error')}")

# Test 3: Search for a common value
print("\n" + "=" * 60)
print("Test 3: Search for 'USA'")
print("-" * 60)
result3 = query_engine.search('USA', column=None, limit=5)
print(f"Status: {result3['status']}")
if result3['status'] == 'success':
    print(f"Found {result3['row_count']} records")
    print(f"Duration: {result3['duration_seconds']}s")
    if result3['data']:
        print(f"\nSample results:")
        for i, record in enumerate(result3['data'][:3], 1):
            print(f"\n  Record {i}:")
            print(f"    ID: {record.get('id', 'N/A')}")
            print(f"    Name: {record.get('name', 'N/A')}")
            print(f"    Country: {record.get('country', 'N/A')}")
else:
    print(f"Error: {result3.get('message', 'Unknown error')}")

# Test 4: Search in email column
print("\n" + "=" * 60)
print("Test 4: Search in 'email' column for '.com'")
print("-" * 60)
result4 = query_engine.search('.com', column='email', limit=10)
print(f"Status: {result4['status']}")
if result4['status'] == 'success':
    print(f"Found {result4['row_count']} records")
    print(f"Duration: {result4['duration_seconds']}s")
else:
    print(f"Error: {result4.get('message', 'Unknown error')}")

print("\n" + "=" * 60)
print("✅ Search tests completed!")
print("=" * 60)
