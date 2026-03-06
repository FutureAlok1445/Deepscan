from sqlalchemy import Column, String, Float, Boolean, JSON, DateTime, Integer, ForeignKey
from sqlalchemy.orm import relationship
import uuid
import datetime
from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    plan = Column(String, default="free") 
    scans_used = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    scans = relationship("Scan", back_populates="owner")

class Scan(Base):
    __tablename__ = "scans"

    id = Column(String, primary_key=True, index=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True) # Allow anonymous scans for now
    status = Column(String, default="pending") # pending, processing, done, failed
    
    # Storage Pointers
    media_path = Column(String, nullable=True)     # Could be S3 path in prod
    heatmap_base64 = Column(String, nullable=True) # Direct base64 string or S3 key
    
    # Results
    ai_score = Column(Float, nullable=True)        # 0.0 to 100.0
    verdict = Column(String, nullable=True)        # Authentic, Uncertain, etc.
    signals = Column(JSON, nullable=True)          # Breakdowns from all layers
    regions_json = Column(JSON, nullable=True)     # Claude Vision polygons
    explainability_text = Column(String, nullable=True)
    
    # Metadata
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="scans")
