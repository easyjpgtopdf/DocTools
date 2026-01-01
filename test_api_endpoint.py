import requests
import sys

API_BASE = "https://pdf-to-word-converter-iwumaktavq-uc.a.run.app"

# Test 1: Root endpoint
print("Test 1: Root endpoint")
try:
    r = requests.get(f"{API_BASE}/", timeout=5)
    print(f"  Status: {r.status_code}")
except Exception as e:
    print(f"  Error: {e}")

# Test 2: Health endpoint
print("\nTest 2: Health endpoint")
try:
    r = requests.get(f"{API_BASE}/api/health", timeout=5)
    print(f"  Status: {r.status_code}")
    print(f"  Response: {r.text[:200]}")
except Exception as e:
    print(f"  Error: {e}")

# Test 3: Convert endpoint (without file - should fail gracefully)
print("\nTest 3: Convert endpoint (GET)")
try:
    r = requests.get(f"{API_BASE}/api/convert/pdf-to-word", timeout=5)
    print(f"  Status: {r.status_code}")
except Exception as e:
    print(f"  Error: {e}")

print("\n API endpoint check complete")
