from fastapi import FastAPI
from core.config import settings
from core.database import Base, engine
from api.endpoints import auth, locations, routes
from models import user, location # Import models so SQLAlchemy knows about them

# We no longer use Base.metadata.create_all(bind=engine) because Alembic handles migrations now!

from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Hız sınırlayıcıyı oluşturuyoruz (IP adresine göre)
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Analyze Instagram Reels descriptions, extract locations using AI, and automatically build travel routes based on geographic proximity."
)

# Rate Limiter'ı uygulamaya bağlıyoruz
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS (Cross-Origin Resource Sharing) Ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Gerçek projelerde buraya domain adresleri yazılır (Örn: "http://localhost:3000")
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(locations.router, prefix="/locations", tags=["Locations (Reels Analysis)"])
app.include_router(routes.router, prefix="/routes", tags=["Travel Routes"])

@app.get("/")
def read_root():
    return {"message": "Welcome to ReelsToRoute AI API!"}
