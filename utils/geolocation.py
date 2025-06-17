from geopy.distance import geodesic
from config import OFFICE_LATITUDE, OFFICE_LONGITUDE, OFFICE_RADIUS

def is_within_office_radius(user_lat: float, user_lon: float) -> bool:
    """
    Check if user's location is within office radius
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
    
    Returns:
        True if user is within office radius, False otherwise
    """
    office_location = (OFFICE_LATITUDE, OFFICE_LONGITUDE)
    user_location = (user_lat, user_lon)
    
    distance = geodesic(office_location, user_location).meters
    
    return distance <= OFFICE_RADIUS

def get_distance_to_office(user_lat: float, user_lon: float) -> float:
    """
    Get distance from user location to office in meters
    
    Args:
        user_lat: User's latitude
        user_lon: User's longitude
    
    Returns:
        Distance in meters
    """
    office_location = (OFFICE_LATITUDE, OFFICE_LONGITUDE)
    user_location = (user_lat, user_lon)
    
    return geodesic(office_location, user_location).meters 