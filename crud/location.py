import math
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload
from models.location import Location, Route
from services import ai_service, map_service


def _validate_ai_data(ai_data: dict) -> tuple[str, str, float, float]:
    if not isinstance(ai_data, dict):
        raise ValueError("AI payload must be a dictionary.")

    name = ai_data.get("name")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("AI payload missing valid location name.")

    description = ai_data.get("description", "")
    if description is None:
        description = ""
    elif not isinstance(description, str):
        description = str(description)

    raw_lat = ai_data.get("latitude")
    raw_lon = ai_data.get("longitude")
    if isinstance(raw_lat, bool) or isinstance(raw_lon, bool):
        raise ValueError("AI payload coordinates must be numbers.")

    try:
        lat = float(raw_lat)
        lon = float(raw_lon)
    except (TypeError, ValueError) as exc:
        raise ValueError("AI payload coordinates must be numeric.") from exc

    if not (math.isfinite(lat) and math.isfinite(lon)):
        raise ValueError("AI payload coordinates must be finite.")
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        raise ValueError("AI payload coordinates out of range.")

    return name.strip(), description.strip(), lat, lon


def _process_location_and_route(db: Session, user_id: int, ai_data: dict):
    name, description, lat, lon = _validate_ai_data(ai_data)

    new_location = Location(
        user_id=user_id,
        name=name,
        description=description,
        latitude=lat,
        longitude=lon,
    )

    # Latitude-aware bounding box (~55 km radius) with antimeridian wrap handling
    lat_margin = 0.5
    lon_margin = lat_margin / max(math.cos(math.radians(lat)), 0.01)

    filters = [
        Location.user_id == user_id,
        Location.latitude.between(max(-90.0, lat - lat_margin), min(90.0, lat + lat_margin)),
    ]

    if lon_margin < 180.0:
        min_lon = lon - lon_margin
        max_lon = lon + lon_margin
        if min_lon < -180.0:
            filters.append(
                or_(
                    Location.longitude >= min_lon + 360.0,
                    Location.longitude <= max_lon,
                )
            )
        elif max_lon > 180.0:
            filters.append(
                or_(
                    Location.longitude >= min_lon,
                    Location.longitude <= max_lon - 360.0,
                )
            )
        else:
            filters.append(Location.longitude.between(min_lon, max_lon))

    past_locations = db.query(Location).filter(*filters).all()

    closest_location = None
    min_distance = float("inf")

    for past_loc in past_locations:
        if map_service.is_nearby(
            new_location.latitude,
            new_location.longitude,
            past_loc.latitude,
            past_loc.longitude,
            max_distance_km=50.0,
        ):
            distance = map_service.calculate_distance_km(
                new_location.latitude,
                new_location.longitude,
                past_loc.latitude,
                past_loc.longitude,
            )
            if distance < min_distance:
                min_distance = distance
                closest_location = past_loc

    if closest_location:
        if closest_location.route_id:
            new_location.route_id = closest_location.route_id
        else:
            new_route = Route(
                user_id=user_id,
                name=f"{closest_location.name} ve Çevresi Rotası",
            )
            db.add(new_route)
            db.flush()

            closest_location.route_id = new_route.id
            new_location.route_id = new_route.id

    db.add(new_location)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(new_location)

    return new_location


def analyze_and_save_location(db: Session, user_id: int, description: str):
    ai_data = ai_service.analyze_location_from_text(description)
    return _process_location_and_route(db, user_id, ai_data)


def analyze_and_save_image_location(
    db: Session,
    user_id: int,
    image_bytes: bytes,
    mime_type: str = "image/jpeg",
):
    ai_data = ai_service.analyze_location_from_image(image_bytes, mime_type=mime_type)
    return _process_location_and_route(db, user_id, ai_data)


def get_user_routes(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(Route)
        .options(selectinload(Route.locations))
        .filter(Route.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_user_locations(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(Location)
        .filter(Location.user_id == user_id)
        .offset(skip)
        .limit(limit)
        .all()
    )
