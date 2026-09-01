from fastapi import FastAPI
from core.config import settings
from core.database import Base, engine
from api.endpoints import auth, locations, routes
from models import user, location # Import models so SQLAlchemy knows about them

# Create database tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Analyze Instagram Reels descriptions, extract locations using AI, and automatically build travel routes based on geographic proximity."
)

# Include Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(locations.router, prefix="/locations", tags=["Locations (Reels Analysis)"])
app.include_router(routes.router, prefix="/routes", tags=["Travel Routes"])

@app.get("/")
def read_root():
    return {"message": "Welcome to ReelsToRoute AI API!"}
