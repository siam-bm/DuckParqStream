"""
Test the API search endpoint directly
"""
import requests
import json

API_BASE = 'http://localhost:8000'

print("=" * 60)
print("Testing Search API Endpoint")
print("=" * 60)

# Test 1: Search with column=null
print("\nTest 1: Search with column=null")
print("-" * 60)
payload = {
    "search_term": "siam",
    "column": None,  # This is Python None, becomes JSON null
    "limit": 100
}

print(f"Payload: {json.dumps(payload)}")

try:
    response = requests.post(
        f"{API_BASE}/query/search",
        json=payload,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status Code: {response.status_code}")
    print(f"Response:")

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=2))
    else:
        print(f"Error Response:")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to API server")
    print("Make sure the server is running: python run.py")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

# Test 2: Search with column specified
print("\n" + "=" * 60)
print("Test 2: Search with column='name'")
print("-" * 60)
payload2 = {
    "search_term": "alice",
    "column": "name",
    "limit": 10
}

print(f"Payload: {json.dumps(payload2)}")

try:
    response = requests.post(
        f"{API_BASE}/query/search",
        json=payload2,
        headers={"Content-Type": "application/json"}
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Found {data.get('row_count', 0)} records")
    else:
        print(f"Error Response:")
        print(response.text)

except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

print("\n" + "=" * 60)
