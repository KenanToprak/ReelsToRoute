import os
from google import genai
from core.config import settings

def analyze_location_from_text(description: str) -> dict:
    """
    Analyzes a description (e.g. from an Instagram Reel) and returns the location name and coordinates.
    """
    if not settings.GEMINI_API_KEY:
        # FAKE/MOCK RESPONSE FOR TESTING WITHOUT API KEY
        print("WARNING: GEMINI_API_KEY is not set. Returning mock data.")
        if "eyfel" in description.lower() or "paris" in description.lower():
            return {"name": "Eiffel Tower", "latitude": 48.8584, "longitude": 2.2945, "description": "Famous tower in Paris"}
        elif "colosseum" in description.lower() or "roma" in description.lower():
            return {"name": "Colosseum", "latitude": 41.8902, "longitude": 12.4922, "description": "Ancient amphitheatre in Rome"}
        else:
            # Default mock
            return {"name": "Unknown Beautiful Place", "latitude": 40.7128, "longitude": -74.0060, "description": "Somewhere nice"}

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    prompt = f"""
    Aşağıdaki Instagram Reels açıklamasına veya metnine bakarak, bahsedilen mekanın neresi olduğunu bul.
    Sadece aşağıdaki formatta JSON döndür, başka hiçbir açıklama yapma:
    {{
        "name": "Mekan Adı",
        "latitude": 0.0000,
        "longitude": 0.0000,
        "description": "Mekan hakkında çok kısa bir bilgi"
    }}
    
    Metin: {description}
    """
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        import json
        # Extract JSON from response text (remove markdown formatting if any)
        text = response.text
        if text.startswith("```json"):
            text = text[7:-3]
        return json.loads(text.strip())
    except Exception as e:
        print(f"AI Service Error: {e}")
        raise ValueError("Could not analyze location from AI.")
