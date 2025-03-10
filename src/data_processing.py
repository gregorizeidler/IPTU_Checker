import googlemaps
import requests
import geopandas as gpd
from shapely.geometry import Point
import json

# Configuration for Google Maps API
API_KEY = "YOUR_GOOGLE_API_KEY"
gmaps = googlemaps.Client(key=API_KEY)

def get_coordinates(address):
    """Get latitude and longitude from an address using Google Maps API."""
    geocode_result = gmaps.geocode(address)
    if geocode_result:
        location = geocode_result[0]["geometry"]["location"]
        return location["lat"], location["lng"]
    return None, None

def get_satellite_image(lat, lng, zoom=19, size="640x640"):
    """Fetch satellite images from Google Static Maps API."""
    url = f"https://maps.googleapis.com/maps/api/staticmap?center={lat},{lng}&zoom={zoom}&size={size}&maptype=satellite&key={API_KEY}"
    response = requests.get(url)
    return response.content if response.status_code == 200 else None
