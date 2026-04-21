import time
import random
import requests
import os

API_BASE_URL = "http://localhost:8000/api/v1"

# A simulated route (e.g., driving down Market St in San Francisco)
ROUTE = [
    (37.7749, -122.4194),
    (37.7750, -122.4180),
    (37.7751, -122.4170),
    (37.7755, -122.4160),
    (37.7760, -122.4150),
    (37.7765, -122.4140),
    (37.7770, -122.4130),
    (37.7775, -122.4120),
    (37.7780, -122.4110),
    (37.7785, -122.4100),
]

DAMAGE_TYPES = [
    ("pothole", "uploads/pothole.png"),
    ("alligator_cracking", "uploads/alligator.png"),
    ("longitudinal_crack", "uploads/crack.png")
]

def upload_image(filepath):
    print(f"📸 Capturing image from edge node... ({filepath})")
    try:
        with open(filepath, 'rb') as f:
            files = {'file': (os.path.basename(filepath), f, 'image/png')}
            response = requests.post(f"{API_BASE_URL}/upload", files=files)
            response.raise_for_status()
            return response.json()['image_url']
    except Exception as e:
        print(f"❌ Failed to upload image: {e}")
        return None

def send_detection(lat, lon, damage_type, severity, image_url):
    payload = {
        "latitude": lat,
        "longitude": lon,
        "damage_type": damage_type,
        "severity_score": severity,
        "image_url": image_url
    }
    try:
        response = requests.post(f"{API_BASE_URL}/detections", json=payload)
        response.raise_for_status()
        print(f"✅ Detection sent! ID: {response.json()['id']} | {damage_type} ({severity*100:.1f}%)")
    except Exception as e:
        print(f"❌ Failed to send detection: {e}")

def run_simulation():
    print("🚗 Starting Fleet Simulator...")
    print("Connecting to SmartRoad API...")
    
    for i, (lat, lon) in enumerate(ROUTE):
        print(f"\n📍 Vehicle at GPS: {lat}, {lon}")
        
        # 60% chance to detect something
        if random.random() < 0.6:
            damage_type, local_image_path = random.choice(DAMAGE_TYPES)
            
            # Severity based on type
            if damage_type == "pothole":
                severity = random.uniform(0.7, 0.99)
            else:
                severity = random.uniform(0.3, 0.8)
                
            print(f"⚠️ Anomaly Detected! Running YOLOv4 inference...")
            time.sleep(1) # simulate inference time
            
            # Upload image to get URL
            image_url = upload_image(local_image_path)
            
            if image_url:
                send_detection(lat, lon, damage_type, severity, image_url)
        else:
            print("✅ Road surface clear.")
            
        time.sleep(3) # simulate driving time to next point
        
    print("\n🏁 Simulation complete. Vehicle has finished route.")

if __name__ == "__main__":
    run_simulation()
