from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from api.endpoints import auth, locations, routes
from core.config import settings
from core.limiter import limiter

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION,
    description="Analyze Instagram Reels descriptions, extract locations using AI, and automatically build travel routes based on geographic proximity.",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
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


@app.get("/health")
def health_check():
    return {"status": "ok"}
