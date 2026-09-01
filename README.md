# ReelsToRoute AI 🌍✈️

ReelsToRoute is an AI-powered travel planning API. It allows users to submit descriptions (or text extracted from Instagram Reels), uses Artificial Intelligence to identify the location and coordinates, and automatically groups nearby locations into sensible Travel Routes.

## Features ✨

*   **AI Location Extraction:** Integrates with Google Gemini (or uses intelligent mocking) to find geographic coordinates from unstructured text/reels descriptions.
*   **Geospatial Routing:** Automatically calculates the Haversine/Geodesic distance between a new location and previously saved locations using `geopy`.
*   **Smart Trip Building:** If a newly discovered place is within 50km of a previously saved place, they are automatically grouped into a Travel Route.
*   **JWT Authentication:** Secure user registration and login system.
*   **FastAPI & PostgreSQL:** High-performance async API with a robust relational database.

## Architecture

*   `models/`: SQLAlchemy database schema (User, Route, Location)
*   `schemas/`: Pydantic models for data validation
*   `crud/`: Core algorithmic logic for distance calculation and route grouping
*   `services/`: External integrations (`ai_service.py` for Gemini, `map_service.py` for Geopy)

## How to Test the AI Feature Locally

1. Create a virtual environment and `pip install -r requirements.txt`.
2. Ensure you have a PostgreSQL database named `reels_route_db` and update `core/config.py` with your credentials.
3. Start the server: `uvicorn main:app --reload`
4. Go to `http://127.0.0.1:8000/docs`
5. **Register & Login** using the `/auth` endpoints.
6. Use the **`POST /locations/analyze`** endpoint.
   * Send a JSON like: `{"description": "Dün izlediğim reelsta Eyfel Kulesi çok güzel görünüyordu."}`
   * The AI service will extract "Eiffel Tower", find its Lat/Lon, and save it.
   * Send another JSON like: `{"description": "Kolezyum etrafında yürüyüş."}`
   * Since Rome is far from Paris, it will be saved separately.
   * Send another JSON like: `{"description": "Louvre müzesi cam piramidi harika."}` (If using real API key). The system will detect it's close to the Eiffel Tower and automatically create a "Paris Route"!

## Note on AI API Key
In `core/config.py`, you can set `GEMINI_API_KEY`. If left empty, the application will use built-in mock AI responses for testing purposes so you don't have to pay for API usage during development.
