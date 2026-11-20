from fastapi.testclient import TestClient
import pytest

from crud import location as crud_location
from models.location import Location, Route
from services import ai_service


def test_analyze_text_rejects_empty_and_whitespace(client: TestClient, auth_headers):
    headers = auth_headers()
    assert client.post("/locations/analyze", json={"description": ""}, headers=headers).status_code == 422
    assert client.post("/locations/analyze", json={"description": "   \n\t  "}, headers=headers).status_code == 422


def test_route_grouping_and_separation(client: TestClient, auth_headers, monkeypatch):
    headers = auth_headers()

    # 1. Paris - Eiffel Tower (mock)
    resp_eiffel = client.post(
        "/locations/analyze",
        json={"description": "Dün izlediğim reelsta Eyfel Kulesi çok güzeldi."},
        headers=headers,
    )
    assert resp_eiffel.status_code == 200
    eiffel = resp_eiffel.json()
    assert eiffel["name"] == "Eiffel Tower"
    assert eiffel["route_id"] is None

    # 2. Rome - Kolezyum (mock, > 1000 km from Paris -> stays ungrouped)
    resp_colosseum = client.post(
        "/locations/analyze",
        json={"description": "Kolezyum etrafında yürüyüş."},
        headers=headers,
    )
    assert resp_colosseum.status_code == 200
    colosseum = resp_colosseum.json()
    assert colosseum["name"] == "Colosseum"
    assert colosseum["route_id"] is None

    # 3. Paris - Louvre (~3 km from Eiffel Tower -> groups into new Route!)
    monkeypatch.setattr(
        ai_service,
        "analyze_location_from_text",
        lambda desc: {
            "name": "Louvre Museum",
            "latitude": 48.8606,
            "longitude": 2.3376,
            "description": "Art museum in Paris",
        },
    )
    resp_louvre = client.post(
        "/locations/analyze",
        json={"description": "Louvre müzesi"},
        headers=headers,
    )
    assert resp_louvre.status_code == 200
    louvre = resp_louvre.json()
    assert louvre["route_id"] is not None

    # Verify routes endpoint includes both Paris locations and not Colosseum
    routes_resp = client.get("/routes/my-routes", headers=headers)
    assert routes_resp.status_code == 200
    routes = routes_resp.json()
    assert len(routes) == 1
    assert routes[0]["estimated_days"] == 1
    loc_names = {loc["name"] for loc in routes[0]["locations"]}
    assert loc_names == {"Eiffel Tower", "Louvre Museum"}


def test_high_latitude_and_antimeridian_grouping(db_session, client: TestClient, auth_headers):
    headers = auth_headers(email="north@example.com")
    # Trigger user creation and resolve user id
    me_loc = client.post(
        "/locations/analyze",
        json={"description": "Paris trip"},
        headers=headers,
    )
    user_id = me_loc.json()["user_id"]

    # High latitude (65°N): ~0.85° longitude difference is ~40 km (< 50 km).
    # Fixed lon_margin=0.6 previously missed this!
    loc1 = crud_location._process_location_and_route(
        db_session,
        user_id,
        {"name": "North Point A", "description": "A", "latitude": 65.0, "longitude": 10.0},
    )
    loc2 = crud_location._process_location_and_route(
        db_session,
        user_id,
        {"name": "North Point B", "description": "B", "latitude": 65.0, "longitude": 10.85},
    )
    assert loc2.route_id is not None
    db_session.refresh(loc1)
    assert loc1.route_id == loc2.route_id

    # Antimeridian wrap: +179.95 and -179.95 at equator are ~11 km apart
    anti1 = crud_location._process_location_and_route(
        db_session,
        user_id,
        {"name": "Fiji East", "description": "E", "latitude": 0.0, "longitude": 179.95},
    )
    anti2 = crud_location._process_location_and_route(
        db_session,
        user_id,
        {"name": "Fiji West", "description": "W", "latitude": 0.0, "longitude": -179.95},
    )
    assert anti2.route_id is not None
    db_session.refresh(anti1)
    assert anti1.route_id == anti2.route_id


def test_deleting_route_preserves_locations_with_null_route_id(db_session, client: TestClient, auth_headers):
    headers = auth_headers(email="cascade@example.com")
    first = client.post("/locations/analyze", json={"description": "Eyfel"}, headers=headers).json()
    second = client.post("/locations/analyze", json={"description": "Paris"}, headers=headers).json()
    route_id = second["route_id"]
    assert route_id is not None

    route_obj = db_session.query(Route).filter(Route.id == route_id).first()
    db_session.delete(route_obj)
    db_session.commit()

    remaining = db_session.query(Location).filter(Location.id.in_([first["id"], second["id"]])).all()
    assert len(remaining) == 2
    assert all(loc.route_id is None for loc in remaining)


def test_atomic_route_creation_rolls_back_on_commit_failure(db_session, client: TestClient, auth_headers):
    headers = auth_headers(email="atomic@example.com")
    first = client.post("/locations/analyze", json={"description": "Eyfel"}, headers=headers).json()
    user_id = first["user_id"]

    original_commit = db_session.commit

    def fail_commit():
        raise RuntimeError("Simulated commit failure")

    db_session.commit = fail_commit
    try:
        with pytest.raises(RuntimeError, match="Simulated commit failure"):
            crud_location._process_location_and_route(
                db_session,
                user_id,
                {"name": "Louvre", "description": "Museum", "latitude": 48.8606, "longitude": 2.3376},
            )
    finally:
        db_session.commit = original_commit

    # No orphaned route should have been persisted
    assert db_session.query(Route).filter(Route.user_id == user_id).count() == 0


def test_image_upload_magic_bytes_mime_forwarding_and_size_limit(
    client: TestClient, auth_headers, monkeypatch
):
    headers = auth_headers(email="img@example.com")
    seen_mimes: list[str] = []

    def fake_image_ai(image_bytes: bytes, mime_type: str = "image/jpeg"):
        seen_mimes.append(mime_type)
        return {
            "name": "Test Monument",
            "latitude": 41.0082,
            "longitude": 28.9784,
            "description": "Istanbul",
        }

    monkeypatch.setattr(ai_service, "analyze_location_from_image", fake_image_ai)

    # Valid PNG magic bytes -> passes image/png
    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 32
    png_resp = client.post(
        "/locations/analyze-image",
        files={"file": ("shot.png", png_bytes, "image/png")},
        headers=headers,
    )
    assert png_resp.status_code == 200
    assert seen_mimes[-1] == "image/png"

    # Valid JPEG magic bytes -> passes image/jpeg
    jpg_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 32
    jpg_resp = client.post(
        "/locations/analyze-image",
        files={"file": ("shot.jpg", jpg_bytes, "image/jpeg")},
        headers=headers,
    )
    assert jpg_resp.status_code == 200
    assert seen_mimes[-1] == "image/jpeg"

    # Spoofed MIME (plain text disguised with Content-Type: image/jpeg) -> 400
    spoof_resp = client.post(
        "/locations/analyze-image",
        files={"file": ("evil.jpg", b"not-a-real-image", "image/jpeg")},
        headers=headers,
    )
    assert spoof_resp.status_code == 400

    # Oversized (> 5MB) -> 413
    oversized = b"\xff\xd8\xff\xe0" + b"a" * (5 * 1024 * 1024 + 10)
    big_resp = client.post(
        "/locations/analyze-image",
        files={"file": ("big.jpg", oversized, "image/jpeg")},
        headers=headers,
    )
    assert big_resp.status_code == 413


def test_user_isolation_and_pagination(client: TestClient, auth_headers):
    headers_a = auth_headers(email="usera@example.com")
    headers_b = auth_headers(email="userb@example.com")

    for i in range(3):
        resp = client.post(
            "/locations/analyze",
            json={"description": f"Unknown spot {i}"},
            headers=headers_a,
        )
        assert resp.status_code == 200

    # User B sees 0 locations
    assert client.get("/locations/my-locations", headers=headers_b).json() == []

    # User A pagination works
    page = client.get("/locations/my-locations?skip=1&limit=1", headers=headers_a)
    assert page.status_code == 200
    assert len(page.json()) == 1


def test_ai_error_returns_502(client: TestClient, auth_headers, monkeypatch):
    headers = auth_headers(email="err502@example.com")

    def broken_ai(desc: str):
        raise ValueError("Upstream Gemini failure")

    monkeypatch.setattr(ai_service, "analyze_location_from_text", broken_ai)
    resp = client.post(
        "/locations/analyze",
        json={"description": "Trigger error"},
        headers=headers,
    )
    assert resp.status_code == 502
