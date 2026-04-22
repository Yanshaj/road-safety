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

app.mount("/", StaticFiles(directory="static", html=True), name="static")
