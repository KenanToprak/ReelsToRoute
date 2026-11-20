# ReelsToRoute AI 🌍✈️

ReelsToRoute is an AI-powered travel planning API built with FastAPI, SQLAlchemy, Alembic, and Google Gemini. It extracts geographic locations from Instagram Reels descriptions or screenshots and automatically groups nearby locations (within 50 km) into travel routes.

## Features ✨

* **AI Location Extraction:** Integrates with Google Gemini (`google-genai`, `gemini-2.5-flash`) with JSON schema output and built-in deterministic mock fallback when `GEMINI_API_KEY` is unset.
* **Vision Location Analysis:** Accepts JPEG and PNG uploads (up to 5 MB, verified by magic bytes) and offloads blocking AI/DB work from the async event loop.
* **Geospatial Routing:** Calculates geodesic distances using `geopy` with latitude-aware bounding-box prefiltering and automatically groups locations within 50 km into routes.
* **JWT Authentication & Rate Limiting:** `bcrypt` password hashing, HS256 JWT bearer tokens, and `slowapi` per-IP rate limiting on auth and AI endpoints.
* **Database Migrations:** Versioned schema management via Alembic (PostgreSQL and SQLite compatible).

## Architecture

* `main.py`: FastAPI application entrypoint, CORS middleware, rate limiter, `/` and `/health` endpoints, router mounting.
* `core/`: Configuration (`config.py`), SQLAlchemy engine/session/naming convention (`database.py`), `slowapi` limiter (`limiter.py`), `bcrypt` + JWT utilities (`security.py`).
* `models/`: SQLAlchemy ORM models (`User`, `Route`, `Location`).
* `schemas/`: Pydantic v2 request/response schemas.
* `crud/`: User creation/lookup (`user.py`) and atomic geospatial location/route grouping (`location.py`).
* `services/`: Gemini text/image extraction (`ai_service.py`) and geodesic distance helpers (`map_service.py`).
* `api/`: JWT dependency (`deps.py`) and route handlers (`endpoints/auth.py`, `endpoints/locations.py`, `endpoints/routes.py`).
* `alembic/`: Database migration environment and version scripts.
* `tests/`: Automated `pytest` test suite.

## Local Setup

1. Create and activate a virtual environment, then install dependencies:
   ```bash
   python -m venv .venv
   # Windows PowerShell: .\.venv\Scripts\Activate.ps1
   # Linux/macOS: source .venv/bin/activate
   pip install -r requirements.txt
   ```
2. Copy `.env.example` to `.env` and configure your environment variables (`DATABASE_URL`, `SECRET_KEY`, `ALLOWED_ORIGINS`, optional `GEMINI_API_KEY`):
   ```bash
   cp .env.example .env
   ```
3. Run database migrations:
   ```bash
   alembic upgrade head
   ```
4. Start the API server:
   ```bash
   uvicorn main:app --reload
   ```
5. Open interactive API docs at `http://127.0.0.1:8000/docs`.

## API Endpoints & Rate Limits

* `GET /` — API welcome message (sync)
* `GET /health` — Health check (`{"status": "ok"}`, sync)
* `POST /auth/register` — Register a new user (`5/minute`, sync)
* `POST /auth/login` — OAuth2 password login returning bearer JWT (`10/minute`, sync)
* `POST /locations/analyze` — Extract and save location from text description (`5/minute`, sync)
* `POST /locations/analyze-image` — Extract and save location from JPEG/PNG upload (`5/minute`, async with `run_in_threadpool`)
* `GET /locations/my-locations` — List saved locations with `skip`/`limit` pagination (sync)
* `GET /routes/my-routes` — List grouped routes and their locations with `skip`/`limit` pagination (sync)

### Mock AI Mode

If `GEMINI_API_KEY` is left empty in `.env`, the application uses built-in mock AI responses (for example, descriptions mentioning `"Eyfel"`/`"Paris"` return Eiffel Tower, `"Kolezyum"`/`"Colosseum"`/`"Roma"` return Colosseum, and image uploads return Statue of Liberty).

## Running Tests

Install development dependencies and run the automated test suite:

```bash
pip install -r requirements-dev.txt
pytest -v
```

## Security Notice

Historical commit `23d5a527` (prior to commit `617a0e70`) contained sample database and JWT secret values in `core/config.py`. If those credentials were ever used in an active database or environment, rotate them immediately.
