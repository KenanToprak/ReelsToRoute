from types import SimpleNamespace
import pytest

from core.config import settings
from services import ai_service, map_service


def test_map_service_distance_and_is_nearby():
    # Eiffel Tower to Louvre (~4.1 km)
    dist = map_service.calculate_distance_km(48.8584, 2.2945, 48.8606, 2.3376)
    assert 3.0 < dist < 5.0
    assert map_service.is_nearby(48.8584, 2.2945, 48.8606, 2.3376, max_distance_km=50.0) is True
    assert map_service.is_nearby(48.8584, 2.2945, 41.8902, 12.4922, max_distance_km=50.0) is False


def test_ai_service_mock_responses(monkeypatch):
    monkeypatch.setattr(settings, "GEMINI_API_KEY", None)

    assert ai_service.analyze_location_from_text("Eyfel Kulesi")["name"] == "Eiffel Tower"
    assert ai_service.analyze_location_from_text("Kolezyum gezisi")["name"] == "Colosseum"
    assert ai_service.analyze_location_from_text("Roma tatili")["name"] == "Colosseum"
    assert ai_service.analyze_location_from_text("Random place")["name"] == "Unknown Beautiful Place"

    img_mock = ai_service.analyze_location_from_image(b"\x89PNG\r\n\x1a\n", mime_type="image/png")
    assert img_mock["name"] == "Özgürlük Heykeli"


def test_ai_service_gemini_json_parsing_and_validation(monkeypatch):
    captured = {}

    class FakeModels:
        def __init__(self, response_text):
            self._response_text = response_text

        def generate_content(self, model, contents, config=None):
            captured["model"] = model
            captured["contents"] = contents
            captured["config"] = config
            return SimpleNamespace(text=self._response_text)

    class FakeClient:
        def __init__(self, api_key):
            captured["api_key"] = api_key
            self.models = FakeModels(captured["next_text"])

    monkeypatch.setattr(settings, "GEMINI_API_KEY", "fake-api-key")
    monkeypatch.setattr(ai_service.genai, "Client", FakeClient)

    # 1. Fenced markdown JSON with trailing newline
    captured["next_text"] = '```json\n{"name": "Galata Tower", "latitude": 41.0256, "longitude": 28.9741, "description": "Historic tower"}\n```\n'
    res = ai_service.analyze_location_from_text("Galata Kulesi")
    assert res == {
        "name": "Galata Tower",
        "latitude": 41.0256,
        "longitude": 28.9741,
        "description": "Historic tower",
    }
    assert "<user_description>" in captured["contents"]
    assert captured["config"].response_mime_type == "application/json"

    # 2. Image analysis preserves PNG MIME type
    captured["next_text"] = '{"name": "Hagia Sophia", "latitude": 41.0086, "longitude": 28.9802, "description": "Landmark"}'
    img_res = ai_service.analyze_location_from_image(b"\x89PNG\r\n\x1a\n", mime_type="image/png")
    assert img_res["name"] == "Hagia Sophia"
    assert captured["contents"][1].inline_data.mime_type == "image/png"

    # 3. None response text raises ValueError
    captured["next_text"] = None
    with pytest.raises(ValueError):
        ai_service.analyze_location_from_text("Galata")

    # 4. Out-of-bounds coordinates raise ValueError
    captured["next_text"] = '{"name": "Invalid", "latitude": 99.0, "longitude": 10.0, "description": "Bad"}'
    with pytest.raises(ValueError):
        ai_service.analyze_location_from_text("Bad coords")

    # 5. Boolean coordinate raises ValueError
    captured["next_text"] = '{"name": "Bool", "latitude": true, "longitude": 10.0, "description": "Bad"}'
    with pytest.raises(ValueError):
        ai_service.analyze_location_from_text("Bool coords")
