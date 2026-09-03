from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from core.database import Base

class Route(Base):
    __tablename__ = "routes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, default="Yeni Gezi Rotası")
    estimated_days = Column(Integer, default=1) # Yeni eklendi!
    created_at = Column(DateTime, default=datetime.utcnow)

    # Bir rotanın birden fazla mekanı olabilir
    locations = relationship("Location", back_populates="route")

class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    route_id = Column(Integer, ForeignKey("routes.id"), nullable=True) # Bir rotaya ait olmayabilir (henüz)
    
    name = Column(String, nullable=False)
    description = Column(String)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    source_image_url = Column(String, nullable=True) # Reels ekran görüntüsü vb.
    created_at = Column(DateTime, default=datetime.utcnow)

    route = relationship("Route", back_populates="locations")
