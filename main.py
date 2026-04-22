import os
import asyncio
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
from fastapi import FastAPI, Depends, status, BackgroundTasks, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from database import get_db, SessionLocal
from models import DetectionEvent, AlertLog
from schemas import DetectionEventCreate, DetectionEventResponse
from twilio.rest import Client

load_dotenv()

# Configure Cloudinary using environment variables
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True
)

app = FastAPI(title="Detection API")

# Add CORS middleware to allow the frontend to fetch data
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def evaluate_and_alert(event_id: int, severity_score: float, damage_type: str):
    if severity_score > 0.85 and damage_type.lower() == 'pothole':
        alert_status = "FAILED"
        try:
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")
            from_number = os.getenv("TWILIO_FROM_NUMBER")
            to_number = os.getenv("ALERT_TO_NUMBER")
            
            if account_sid and auth_token and from_number and to_number:
                client = Client(account_sid, auth_token)
                
                # Run sync twilio call in a thread pool to avoid blocking the async event loop
                def send_sms():
                    client.messages.create(
                        body=f"High severity pothole detected (Event ID: {event_id}, Severity: {severity_score})",
                        from_=from_number,
                        to=to_number
                    )
                
                await asyncio.to_thread(send_sms)
                alert_status = "SENT"
            else:
                alert_status = "SKIPPED_MISSING_CREDENTIALS"
        except Exception as e:
            alert_status = f"FAILED: {str(e)}"
            
        async with SessionLocal() as session:
            alert_log = AlertLog(event_id=event_id, alert_status=alert_status)
            session.add(alert_log)
            await session.commit()

@app.post("/api/v1/detections", status_code=status.HTTP_201_CREATED)
async def create_detection(event: DetectionEventCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    new_event = DetectionEvent(
        latitude=event.latitude,
        longitude=event.longitude,
        damage_type=event.damage_type,
        severity_score=event.severity_score,
        image_url=event.image_url
    )
    db.add(new_event)
    await db.commit()
    await db.refresh(new_event)
    
    background_tasks.add_task(evaluate_and_alert, new_event.id, new_event.severity_score, new_event.damage_type)
    
    return {"id": new_event.id}

@app.post("/api/v1/upload")
async def upload_image(file: UploadFile = File(...)):
    """Upload image to Cloudinary for permanent cloud storage."""
    try:
        contents = await file.read()
        # Upload to Cloudinary — returns a permanent HTTPS URL
        result = await asyncio.to_thread(
            cloudinary.uploader.upload,
            contents,
            folder="smartroad",
            resource_type="image"
        )
        return {"image_url": result["secure_url"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image upload failed: {str(e)}")

@app.get("/api/v1/detections", response_model=List[DetectionEventResponse])
async def get_detections(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DetectionEvent).order_by(DetectionEvent.timestamp.desc()))
    return result.scalars().all()

# ─── Training / Seed Data ────────────────────────────────────────────────────

SEED_EVENTS = [
    # Chandigarh
    {"latitude": 30.7333, "longitude": 76.7794, "damage_type": "pothole",            "severity_score": 0.95, "image_url": None},
    {"latitude": 30.7270, "longitude": 76.7700, "damage_type": "pothole",            "severity_score": 0.91, "image_url": None},
    {"latitude": 30.7400, "longitude": 76.7850, "damage_type": "alligator_cracking", "severity_score": 0.78, "image_url": None},
    {"latitude": 30.7100, "longitude": 76.7600, "damage_type": "longitudinal_crack", "severity_score": 0.42, "image_url": None},
    {"latitude": 30.7500, "longitude": 76.7900, "damage_type": "pothole",            "severity_score": 0.88, "image_url": None},
    {"latitude": 30.7200, "longitude": 76.8000, "damage_type": "alligator_cracking", "severity_score": 0.65, "image_url": None},
    # Delhi
    {"latitude": 28.6200, "longitude": 77.2100, "damage_type": "pothole",            "severity_score": 0.97, "image_url": None},
    {"latitude": 28.6350, "longitude": 77.2250, "damage_type": "pothole",            "severity_score": 0.89, "image_url": None},
    {"latitude": 28.6100, "longitude": 77.1980, "damage_type": "alligator_cracking", "severity_score": 0.72, "image_url": None},
    {"latitude": 28.6500, "longitude": 77.2400, "damage_type": "longitudinal_crack", "severity_score": 0.45, "image_url": None},
    {"latitude": 28.5800, "longitude": 77.1800, "damage_type": "pothole",            "severity_score": 0.86, "image_url": None},
    {"latitude": 28.6700, "longitude": 77.2600, "damage_type": "alligator_cracking", "severity_score": 0.61, "image_url": None},
    # Mumbai
    {"latitude": 19.0800, "longitude": 72.8800, "damage_type": "pothole",            "severity_score": 0.99, "image_url": None},
    {"latitude": 19.0700, "longitude": 72.8700, "damage_type": "pothole",            "severity_score": 0.92, "image_url": None},
    {"latitude": 19.0900, "longitude": 72.8900, "damage_type": "alligator_cracking", "severity_score": 0.83, "image_url": None},
    {"latitude": 19.0650, "longitude": 72.8650, "damage_type": "longitudinal_crack", "severity_score": 0.55, "image_url": None},
    {"latitude": 19.1000, "longitude": 72.9000, "damage_type": "pothole",            "severity_score": 0.87, "image_url": None},
    {"latitude": 19.0550, "longitude": 72.8550, "damage_type": "alligator_cracking", "severity_score": 0.67, "image_url": None},
    # Bengaluru
    {"latitude": 12.9800, "longitude": 77.6000, "damage_type": "pothole",            "severity_score": 0.90, "image_url": None},
    {"latitude": 12.9600, "longitude": 77.5800, "damage_type": "alligator_cracking", "severity_score": 0.74, "image_url": None},
    {"latitude": 12.9900, "longitude": 77.6100, "damage_type": "longitudinal_crack", "severity_score": 0.39, "image_url": None},
    {"latitude": 12.9500, "longitude": 77.5700, "damage_type": "pothole",            "severity_score": 0.85, "image_url": None},
    {"latitude": 13.0000, "longitude": 77.6200, "damage_type": "alligator_cracking", "severity_score": 0.58, "image_url": None},
    # Pune
    {"latitude": 18.5300, "longitude": 73.8600, "damage_type": "pothole",            "severity_score": 0.94, "image_url": None},
    {"latitude": 18.5100, "longitude": 73.8400, "damage_type": "pothole",            "severity_score": 0.88, "image_url": None},
    {"latitude": 18.5400, "longitude": 73.8700, "damage_type": "alligator_cracking", "severity_score": 0.70, "image_url": None},
    {"latitude": 18.5000, "longitude": 73.8300, "damage_type": "longitudinal_crack", "severity_score": 0.47, "image_url": None},
    {"latitude": 18.5500, "longitude": 73.8800, "damage_type": "pothole",            "severity_score": 0.82, "image_url": None},
    # Hyderabad
    {"latitude": 17.3850, "longitude": 78.4867, "damage_type": "pothole",            "severity_score": 0.93, "image_url": None},
    {"latitude": 17.3950, "longitude": 78.4967, "damage_type": "longitudinal_crack", "severity_score": 0.36, "image_url": None},
]

@app.post("/api/v1/seed", status_code=status.HTTP_201_CREATED)
async def seed_training_data(db: AsyncSession = Depends(get_db)):
    """Insert 30 sample road damage events across 5 Indian cities for demo/training."""
    events = [DetectionEvent(**ev) for ev in SEED_EVENTS]
    db.add_all(events)
    await db.commit()
    return {"message": f"✅ Seeded {len(events)} training events successfully.", "count": len(events)}

@app.delete("/api/v1/seed", status_code=status.HTTP_200_OK)
async def clear_all_detections(db: AsyncSession = Depends(get_db)):
    """Delete ALL detection events (use with caution — for reset/demo purposes)."""
    result = await db.execute(select(DetectionEvent))
    all_events = result.scalars().all()
    for ev in all_events:
        await db.delete(ev)
    await db.commit()
    return {"message": f"🗑 Deleted {len(all_events)} events."}

app.mount("/", StaticFiles(directory="static", html=True), name="static")
