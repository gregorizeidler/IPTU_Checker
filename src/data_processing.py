import googlemaps
import requests
import os
import sys
from pathlib import Path
from geopy.geocoders import Nominatim

# Add config to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.api_keys import API_KEY

# Initialize Google Maps client
GOOGLE_MAPS_AVAILABLE = False
if API_KEY and API_KEY != "YOUR_GOOGLE_MAPS_API_KEY":
    try:
        gmaps = googlemaps.Client(key=API_KEY)
        GOOGLE_MAPS_AVAILABLE = True
        print("✅ Google Maps API configured")
    except Exception as e:
        print(f"⚠️  Google Maps API error: {e}")
        GOOGLE_MAPS_AVAILABLE = False
else:
    print("⚠️  Google Maps API not configured, will use OpenStreetMap")
    gmaps = None

# Initialize OpenStreetMap geocoder (free alternative)
osm_geocoder = Nominatim(user_agent="iptu_checker_app")

def get_coordinates_osm(address):
    """
    Get coordinates using OpenStreetMap (free alternative).
    
    Args:
        address (str): Full address to geocode
        
    Returns:
        tuple: (latitude, longitude) or (None, None) if not found
    """
    try:
        location = osm_geocoder.geocode(address)
        if location:
            lat, lng = location.latitude, location.longitude
            print(f"🗺️  OSM coordinates for {address}: ({lat}, {lng})")
            return lat, lng
        else:
            print(f"❌ Address not found in OpenStreetMap: {address}")
            return None, None
    except Exception as e:
        print(f"❌ Error geocoding with OSM '{address}': {e}")
        return None, None

def get_coordinates(address, use_osm=False):
    """
    Get latitude and longitude from an address.
    Tries Google Maps API first, falls back to OpenStreetMap if not available.
    
    Args:
        address (str): Full address to geocode
        use_osm (bool): Force use of OpenStreetMap instead of Google Maps
        
    Returns:
        tuple: (latitude, longitude) or (None, None) if not found
    """
    # Use OpenStreetMap if requested or if Google Maps is not available
    if use_osm or not GOOGLE_MAPS_AVAILABLE:
        return get_coordinates_osm(address)
    
    # Try Google Maps API
    try:
        geocode_result = gmaps.geocode(address)
        if geocode_result:
            location = geocode_result[0]["geometry"]["location"]
            lat, lng = location["lat"], location["lng"]
            print(f"🗺️  Google Maps coordinates for {address}: ({lat}, {lng})")
            return lat, lng
        else:
            # Fallback to OpenStreetMap
            print(f"⚠️  Address not found in Google Maps, trying OpenStreetMap...")
            return get_coordinates_osm(address)
    except Exception as e:
        print(f"❌ Error geocoding address '{address}': {e}")
        # Fallback to OpenStreetMap
        print(f"   Trying OpenStreetMap as fallback...")
        return get_coordinates_osm(address)

def get_satellite_image(lat, lng, zoom=19, size="640x640", output_path=None, 
                        source='google'):
    """
    Fetch satellite images from Google Static Maps API or Earth Engine.
    
    Args:
        lat (float): Latitude
        lng (float): Longitude
        zoom (int): Zoom level (1-20, default 19 for high detail)
        size (str): Image size in format "widthxheight" (max 640x640 for free tier)
        output_path (str): Path to save the image. If None, returns raw bytes.
        source (str): 'google', 'sentinel2', or 'landsat8'
        
    Returns:
        bytes or bool: Image content or True if saved successfully
    """
    # Use Earth Engine for Sentinel-2 or Landsat-8
    if source in ['sentinel2', 'landsat8']:
        try:
            from earth_engine_utils import get_satellite_image_ee
            result = get_satellite_image_ee(lat, lng, output_path, satellite=source)
            return result
        except ImportError:
            print("⚠️  Earth Engine utils not available, falling back to Google Maps")
            source = 'google'
    
    # Use Google Maps Static API
    if source == 'google':
        if not GOOGLE_MAPS_AVAILABLE:
            print("❌ Google Maps API not configured")
            return None
        
        try:
            url = (
                f"https://maps.googleapis.com/maps/api/staticmap?"
                f"center={lat},{lng}&zoom={zoom}&size={size}"
                f"&maptype=satellite&key={API_KEY}"
            )
            
            response = requests.get(url)
            
            if response.status_code == 200:
                print(f"🛰️  Downloaded Google Maps satellite image for ({lat}, {lng})")
                
                if output_path:
                    with open(output_path, 'wb') as f:
                        f.write(response.content)
                    print(f"   Saved to: {output_path}")
                    return True
                else:
                    return response.content
            else:
                print(f"❌ Failed to fetch satellite image: HTTP {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error fetching satellite image: {e}")
            return None

def load_properties_from_csv(csv_path):
    """
    Load property data from a CSV file.
    Expected columns: address, registered_area, owner (optional)
    
    Args:
        csv_path (str): Path to CSV file
        
    Returns:
        list: List of property dictionaries
    """
    import pandas as pd
    
    try:
        df = pd.read_csv(csv_path)
        properties = df.to_dict('records')
        print(f"📋 Loaded {len(properties)} properties from {csv_path}")
        return properties
    except Exception as e:
        print(f"❌ Error loading CSV: {e}")
        return []

def get_sample_properties():
    """
    Get sample property data for testing.
    In production, replace this with real municipal cadastral data.
    """
    return [
        {
            "address": "Avenida Paulista, 1000, São Paulo, SP, Brasil",
            "registered_area": 500.0,  # m²
            "owner": "João Silva"
        },
        {
            "address": "Rua Augusta, 2000, São Paulo, SP, Brasil",
            "registered_area": 450.0,
            "owner": "Pedro Costa"
        },
        {
            "address": "Rua Oscar Freire, 300, São Paulo, SP, Brasil",
            "registered_area": 280.0,
            "owner": "Carlos Ferreira"
        },
    ]
