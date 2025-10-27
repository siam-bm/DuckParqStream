"""
Test search after fix - Run AFTER restarting the API server
"""
import requests
import json

API_BASE = 'http://localhost:8000'

print("=" * 70)
print("Testing Search API - After Fix")
print("=" * 70)

tests = [
    {
        "name": "Search with column=null (all columns)",
        "payload": {"search_term": "siam", "column": None, "limit": 100}
    },
    {
        "name": "Search with column=null for 'USA'",
        "payload": {"search_term": "USA", "column": None, "limit": 10}
    },
    {
        "name": "Search specific column 'name'",
        "payload": {"search_term": "alice", "column": "name", "limit": 10}
    },
    {
        "name": "Search specific column 'email'",
        "payload": {"search_term": "@example.com", "column": "email", "limit": 5}
    },
    {
        "name": "Search with special characters",
        "payload": {"search_term": "user_", "column": None, "limit": 5}
    }
]

for i, test in enumerate(tests, 1):
    print(f"\n{'='*70}")
    print(f"Test {i}: {test['name']}")
    print(f"{'='*70}")
    print(f"Payload: {json.dumps(test['payload'])}")

    try:
        response = requests.post(
            f"{API_BASE}/query/search",
            json=test['payload'],
            timeout=10
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"✅ SUCCESS")
            print(f"   Found: {data.get('row_count', 0)} records")
            print(f"   Duration: {data.get('duration_seconds', 0)}s")
            if data.get('query'):
                query_preview = data['query'][:100].replace('\n', ' ')
                print(f"   Query: {query_preview}...")
        else:
            print(f"❌ FAILED")
            print(f"   Response: {response.text[:200]}")

    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Cannot connect to API")
        print("   Please make sure the server is running:")
        print("   python run.py")
        break
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")

print(f"\n{'='*70}")
print("Test Summary")
print(f"{'='*70}")
print("\nIf all tests passed, your search functionality is working correctly!")
print("\nNext steps:")
print("1. Try it in the web UI: http://localhost:8000")
print("2. Use the Search tab to test different queries")
print("3. Try with 'column' empty (searches all) or specify a column name")
