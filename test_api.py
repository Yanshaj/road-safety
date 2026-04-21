import urllib.request
import json
import time

url = "http://localhost:8000/api/v1/detections"

# This payload should trigger the background task because severity > 0.85 and damage_type == 'pothole'
payload = {
    "latitude": 37.7749,
    "longitude": -122.4194,
    "damage_type": "pothole",
    "severity_score": 0.95,
    "image_url": "https://example.com/severe_pothole.jpg"
}

print(f"Sending POST request to {url}...")
req = urllib.request.Request(
    url, 
    data=json.dumps(payload).encode('utf-8'), 
    headers={'Content-Type': 'application/json'}
)

try:
    start_time = time.time()
    with urllib.request.urlopen(req) as response:
        response_data = json.loads(response.read().decode())
        elapsed = time.time() - start_time
        
        print(f"✅ Success! Status Code: {response.getcode()}")
        print(f"⏱️  Endpoint returned instantly in {elapsed:.4f} seconds (Background task is running asynchronously).")
        print(f"📦 Response Data: {response_data}")
except Exception as e:
    print(f"❌ Error: {e}")
