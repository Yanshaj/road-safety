from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class DetectionEvent(Base):
    __tablename__ = "detection_events"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    damage_type = Column(String, index=True, nullable=False)
    severity_score = Column(Float, nullable=False)
    image_url = Column(String, nullable=True)

    alert_logs = relationship("AlertLog", back_populates="detection_event")

class AlertLog(Base):
    __tablename__ = "alert_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("detection_events.id"), nullable=False)
    alert_status = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    detection_event = relationship("DetectionEvent", back_populates="alert_logs")
