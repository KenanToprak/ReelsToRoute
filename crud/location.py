from sqlalchemy.orm import Session
from models.location import Location, Route
from schemas.location import LocationCreate
from services import ai_service, map_service

def _process_location_and_route(db: Session, user_id: int, ai_data: dict):
    # 2. Yeni mekan objesini oluştur
    new_location = Location(
        user_id=user_id,
        name=ai_data["name"],
        description=ai_data["description"],
        latitude=ai_data["latitude"],
        longitude=ai_data["longitude"]
    )
    
    # 3. Kullanıcının önceki mekanlarını getir (Milyonlarca kayıt olabileceği için Bounding Box Optimizasyonu kullanıyoruz)
    lat_margin = 0.5 # ~55 km sınır
    lon_margin = 0.6 # ~55 km sınır (ekvatordan uzaklaştıkça değişir ama güvenli marj)
    
    past_locations = db.query(Location).filter(
        Location.user_id == user_id,
        Location.latitude.between(new_location.latitude - lat_margin, new_location.latitude + lat_margin),
        Location.longitude.between(new_location.longitude - lon_margin, new_location.longitude + lon_margin)
    ).all()
    
    closest_location = None
    min_distance = float('inf')
    
    # 4. En yakın mekanı bul (Maksimum 50km sınırı ile)
    for past_loc in past_locations:
        distance = map_service.calculate_distance_km(
            new_location.latitude, new_location.longitude,
            past_loc.latitude, past_loc.longitude
        )
        if distance < 50.0 and distance < min_distance:
            min_distance = distance
            closest_location = past_loc
            
    # 5. Rota (Trip) Mantığı
    if closest_location:
        # Eğer yakındaki eski mekanın zaten bir rotası varsa, yeni mekanı da o rotaya ekle
        if closest_location.route_id:
            new_location.route_id = closest_location.route_id
        else:
            # İki mekan birbirine yakın ama henüz rotaları yoksa, YENİ ROTA oluştur
            new_route = Route(user_id=user_id, name=f"{closest_location.name} ve Çevresi Rotası")
            db.add(new_route)
            db.commit()
            db.refresh(new_route)
            
            # Eski mekanı da yeni rotaya dahil et
            closest_location.route_id = new_route.id
            new_location.route_id = new_route.id
            
    # 6. Veritabanına kaydet
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    
    return new_location

def analyze_and_save_location(db: Session, user_id: int, description: str):
    # 1. AI ile mekanı bul (Metin)
    ai_data = ai_service.analyze_location_from_text(description)
    return _process_location_and_route(db, user_id, ai_data)

def analyze_and_save_image_location(db: Session, user_id: int, image_bytes: bytes):
    # 1. AI ile mekanı bul (Görsel)
    ai_data = ai_service.analyze_location_from_image(image_bytes)
    return _process_location_and_route(db, user_id, ai_data)

def get_user_routes(db: Session, user_id: int):
    return db.query(Route).filter(Route.user_id == user_id).all()

def get_user_locations(db: Session, user_id: int):
    return db.query(Location).filter(Location.user_id == user_id).all()
