"""
CLI test tool — simulates the full CSI platform flow without a router.

Usage:
  python tools/test_flow.py --base-url http://localhost:8000

Requires env vars or prompts for auth credentials.
"""
import requests, json, sys, os, time, numpy as np

BASE = os.environ.get("API_URL", "http://localhost:8000")

def main():
    email = os.environ.get("TEST_EMAIL") or input("Email: ")
    password = os.environ.get("TEST_PASSWORD") or input("Password: ")
    s = requests.Session()
    r = s.post(f"{BASE}/auth/login", json={"email": email, "password": password})
    r.raise_for_status()
    token = r.json()["access_token"]
    s.headers.update({"Authorization": f"Bearer {token}"})
    print("Logged in")

    homes = s.get(f"{BASE}/homes").json()
    if not homes:
        h = s.post(f"{BASE}/homes", json={"name": "Test Home", "address": ""}).json()
        home_id = h["id"]
        print(f"Created home {home_id[:8]}...")
    else:
        home_id = homes[0]["id"]
        print(f"Using home {home_id[:8]}...")

    r = s.post(f"{BASE}/devices/pair", params={"home_id": home_id}, json={"gateway_id": "cli-test", "firmware_ver": "test"})
    if r.status_code == 409:
        print("Device already paired")
    else:
        r.raise_for_status()
        print("Device paired")

    print("Simulating 10 normal packets...")
    for i in range(10):
        amp = np.random.randn(3, 52).astype(np.float32)
        r = s.post(f"{BASE}/devices/events", json={
            "gateway_id": "cli-test",
            "event_type": "normal",
            "csi_data_hex": amp.tobytes().hex(),
        })
        r.raise_for_status()
        print(f"  normal {i+1}: conf={r.json().get('confidence')}")

    print("Simulating intrusion...")
    amp = (np.random.randn(3, 52) * 0.3 + 3.0).astype(np.float32)
    r = s.post(f"{BASE}/devices/events", json={
        "gateway_id": "cli-test",
        "event_type": "unknown",
        "csi_data_hex": amp.tobytes().hex(),
    })
    print(f"  intrusion: {r.json()}")

    print("\nFetching events...")
    events = s.get(f"{BASE}/events/{home_id}?limit=20").json()
    print(f"  {len(events.get('events',[]))} events found")

    api_key = s.post(f"{BASE}/api-keys", json={"label": "test-key", "permissions": "read_only"}).json()
    print(f"API key: {api_key.get('key','')[:20]}...")

    r = s.post(f"{BASE}/arming/override", params={"home_id": home_id, "armed": True})
    print(f"Arming: {r.json()}")

    r = s.post(f"{BASE}/arming/override", params={"home_id": home_id, "armed": False})
    print(f"Disarming: {r.json()}")

    r = s.get(f"{BASE}/health")
    print(f"\nHealth: {r.json()}")
    print("Done")

if __name__ == "__main__":
    main()
