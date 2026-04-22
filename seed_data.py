"""
seed_data.py — Run this locally to populate the database with sample training data.
Usage: python seed_data.py
"""
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

# Must be set before importing database
from database import SessionLocal
from models import DetectionEvent

# 30 realistic Indian city road damage detections
SEED_EVENTS = [
    # Chandigarh area (30.6854, 76.6653 area — matches existing data)
    {"latitude": 30.7333, "longitude": 76.7794, "damage_type": "pothole",              "severity_score": 0.95, "image_url": "https://res.cloudinary.com/demo/image/upload/v1/samples/landscapes/nature-mountains.jpg"},
    {"latitude": 30.7270, "longitude": 76.7700, "damage_type": "pothole",              "severity_score": 0.91, "image_url": None},
    {"latitude": 30.7400, "longitude": 76.7850, "damage_type": "alligator_cracking",   "severity_score": 0.78, "image_url": None},
    {"latitude": 30.7100, "longitude": 76.7600, "damage_type": "longitudinal_crack",   "severity_score": 0.42, "image_url": None},
    {"latitude": 30.7500, "longitude": 76.7900, "damage_type": "pothole",              "severity_score": 0.88, "image_url": None},
    {"latitude": 30.7200, "longitude": 76.8000, "damage_type": "alligator_cracking",   "severity_score": 0.65, "image_url": None},
    {"latitude": 30.6900, "longitude": 76.7500, "damage_type": "longitudinal_crack",   "severity_score": 0.38, "image_url": None},
    {"latitude": 30.7600, "longitude": 76.8100, "damage_type": "pothole",              "severity_score": 0.93, "image_url": None},

    # Delhi area (28.6139, 77.2090)
    {"latitude": 28.6200, "longitude": 77.2100, "damage_type": "pothole",              "severity_score": 0.97, "image_url": None},
    {"latitude": 28.6350, "longitude": 77.2250, "damage_type": "pothole",              "severity_score": 0.89, "image_url": None},
    {"latitude": 28.6100, "longitude": 77.1980, "damage_type": "alligator_cracking",   "severity_score": 0.72, "image_url": None},
    {"latitude": 28.6500, "longitude": 77.2400, "damage_type": "longitudinal_crack",   "severity_score": 0.45, "image_url": None},
    {"latitude": 28.5800, "longitude": 77.1800, "damage_type": "pothole",              "severity_score": 0.86, "image_url": None},
    {"latitude": 28.6700, "longitude": 77.2600, "damage_type": "alligator_cracking",   "severity_score": 0.61, "image_url": None},

    # Mumbai area (19.0760, 72.8777)
    {"latitude": 19.0800, "longitude": 72.8800, "damage_type": "pothole",              "severity_score": 0.99, "image_url": None},
    {"latitude": 19.0700, "longitude": 72.8700, "damage_type": "pothole",              "severity_score": 0.92, "image_url": None},
    {"latitude": 19.0900, "longitude": 72.8900, "damage_type": "alligator_cracking",   "severity_score": 0.83, "image_url": None},
    {"latitude": 19.0650, "longitude": 72.8650, "damage_type": "longitudinal_crack",   "severity_score": 0.55, "image_url": None},
    {"latitude": 19.1000, "longitude": 72.9000, "damage_type": "pothole",              "severity_score": 0.87, "image_url": None},
    {"latitude": 19.0550, "longitude": 72.8550, "damage_type": "alligator_cracking",   "severity_score": 0.67, "image_url": None},

    # Bengaluru area (12.9716, 77.5946)
    {"latitude": 12.9800, "longitude": 77.6000, "damage_type": "pothole",              "severity_score": 0.90, "image_url": None},
    {"latitude": 12.9600, "longitude": 77.5800, "damage_type": "alligator_cracking",   "severity_score": 0.74, "image_url": None},
    {"latitude": 12.9900, "longitude": 77.6100, "damage_type": "longitudinal_crack",   "severity_score": 0.39, "image_url": None},
    {"latitude": 12.9500, "longitude": 77.5700, "damage_type": "pothole",              "severity_score": 0.85, "image_url": None},
    {"latitude": 13.0000, "longitude": 77.6200, "damage_type": "alligator_cracking",   "severity_score": 0.58, "image_url": None},

    # Pune area (18.5204, 73.8567)
    {"latitude": 18.5300, "longitude": 73.8600, "damage_type": "pothole",              "severity_score": 0.94, "image_url": None},
    {"latitude": 18.5100, "longitude": 73.8400, "damage_type": "pothole",              "severity_score": 0.88, "image_url": None},
    {"latitude": 18.5400, "longitude": 73.8700, "damage_type": "alligator_cracking",   "severity_score": 0.70, "image_url": None},
    {"latitude": 18.5000, "longitude": 73.8300, "damage_type": "longitudinal_crack",   "severity_score": 0.47, "image_url": None},
    {"latitude": 18.5500, "longitude": 73.8800, "damage_type": "pothole",              "severity_score": 0.82, "image_url": None},
]

async def seed():
    print(f"🌱 Seeding {len(SEED_EVENTS)} training events into the database...")
    async with SessionLocal() as session:
        for i, ev in enumerate(SEED_EVENTS):
            event = DetectionEvent(**ev)
            session.add(event)
            print(f"  [{i+1:02d}/{len(SEED_EVENTS)}] {ev['damage_type']:25s} severity={ev['severity_score']:.2f}  lat={ev['latitude']}")
        await session.commit()
    print(f"\n✅ Done! {len(SEED_EVENTS)} events added.")
    print("👉 Open your dashboard to see them: http://localhost:8000/dashboard.html")

if __name__ == "__main__":
    asyncio.run(seed())
