from geopy.distance import geodesic

def calculate_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the geodesic distance between two points on Earth in kilometers.
    """
    coord1 = (lat1, lon1)
    coord2 = (lat2, lon2)
    
    # Returns the distance in kilometers
    return geodesic(coord1, coord2).kilometers

def is_nearby(lat1: float, lon1: float, lat2: float, lon2: float, max_distance_km: float = 50.0) -> bool:
    """
    Checks if two coordinates are within a specified maximum distance (default 50km).
    """
    distance = calculate_distance_km(lat1, lon1, lat2, lon2)
    return distance <= max_distance_km
