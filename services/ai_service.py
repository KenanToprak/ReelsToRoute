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
        text = response.text
        if text.startswith("```json"):
            text = text[7:-3]
        return json.loads(text.strip())
    except Exception as e:
        print(f"AI Service Error: {e}")
        raise ValueError("Could not analyze location from AI.")

def analyze_location_from_image(image_bytes: bytes) -> dict:
    """
    Analyzes an image (e.g. from an Instagram Reel screenshot) and returns the location name and coordinates.
    Requires GEMINI_API_KEY to be set.
    """
    if not settings.GEMINI_API_KEY:
        print("WARNING: GEMINI_API_KEY is not set. Returning mock data for image.")
        return {"name": "Özgürlük Heykeli", "latitude": 40.6892, "longitude": -74.0445, "description": "New York'ta ikonik bir anıt."}

    client = genai.Client(api_key=settings.GEMINI_API_KEY)
    
    prompt = """
    Bu fotoğrafa bakarak, bahsedilen veya gösterilen mekanın (turistik yer, şehir, anıt vb.) tam olarak neresi olduğunu bul.
    Eğer bulamazsan en mantıklı tahmini yap.
    Sadece aşağıdaki formatta JSON döndür, başka hiçbir açıklama yapma:
    {
        "name": "Mekan Adı",
        "latitude": 0.0000,
        "longitude": 0.0000,
        "description": "Mekan hakkında çok kısa bir bilgi"
    }
    """
    
    try:
        from google.genai import types
        # Create an image part from bytes
        # We assume it's a jpeg/png for general use
        image_part = types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg')
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[prompt, image_part],
        )
        import json
        text = response.text
        if text.startswith("```json"):
            text = text[7:-3]
        return json.loads(text.strip())
    except Exception as e:
        print(f"Vision AI Error: {e}")
        raise ValueError("Could not analyze image from AI.")
