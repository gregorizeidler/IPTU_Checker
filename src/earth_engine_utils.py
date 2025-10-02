"""
Google Earth Engine integration for satellite imagery
Supports Sentinel-2 and Landsat-8 data collection
"""

import os
import json

try:
    import ee
    EE_AVAILABLE = True
except ImportError:
    EE_AVAILABLE = False
    print("⚠️  Google Earth Engine not installed. Install with: pip install earthengine-api")

def initialize_earth_engine(credentials_path=None):
    """
    Initialize Google Earth Engine.
    
    Args:
        credentials_path (str): Path to service account credentials JSON
        
    Returns:
        bool: True if initialized successfully
    """
    if not EE_AVAILABLE:
        print("❌ Earth Engine library not available")
        return False
    
    try:
        # Try to initialize with existing credentials
        ee.Initialize()
        print("✅ Earth Engine initialized successfully")
        return True
    except:
        try:
            # Try authenticating
            print("🔐 Authenticating Earth Engine...")
            print("   This will open a browser window for authentication")
            ee.Authenticate()
            ee.Initialize()
            print("✅ Earth Engine authenticated and initialized")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize Earth Engine: {e}")
            print("   Run 'earthengine authenticate' in terminal first")
            return False

def get_sentinel2_image(lat, lng, start_date='2023-01-01', end_date='2024-12-31', 
                        cloud_cover_max=20):
    """
    Get Sentinel-2 satellite imagery for a location.
    
    Args:
        lat (float): Latitude
        lng (float): Longitude
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        cloud_cover_max (int): Maximum cloud cover percentage
        
    Returns:
        ee.Image or None: Sentinel-2 image
    """
    if not EE_AVAILABLE:
        return None
    
    try:
        # Define point of interest
        point = ee.Geometry.Point([lng, lat])
        
        # Load Sentinel-2 surface reflectance data
        sentinel = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') \
            .filterBounds(point) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', cloud_cover_max)) \
            .sort('CLOUDY_PIXEL_PERCENTAGE')
        
        # Get the least cloudy image
        image = sentinel.first()
        
        if image is None:
            print(f"⚠️  No Sentinel-2 images found for ({lat}, {lng})")
            return None
        
        print(f"🛰️  Found Sentinel-2 image for ({lat}, {lng})")
        return image
        
    except Exception as e:
        print(f"❌ Error fetching Sentinel-2 image: {e}")
        return None

def get_landsat8_image(lat, lng, start_date='2023-01-01', end_date='2024-12-31',
                       cloud_cover_max=20):
    """
    Get Landsat-8 satellite imagery for a location.
    
    Args:
        lat (float): Latitude
        lng (float): Longitude
        start_date (str): Start date in YYYY-MM-DD format
        end_date (str): End date in YYYY-MM-DD format
        cloud_cover_max (int): Maximum cloud cover percentage
        
    Returns:
        ee.Image or None: Landsat-8 image
    """
    if not EE_AVAILABLE:
        return None
    
    try:
        # Define point of interest
        point = ee.Geometry.Point([lng, lat])
        
        # Load Landsat-8 surface reflectance data
        landsat = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
            .filterBounds(point) \
            .filterDate(start_date, end_date) \
            .filter(ee.Filter.lt('CLOUD_COVER', cloud_cover_max)) \
            .sort('CLOUD_COVER')
        
        # Get the least cloudy image
        image = landsat.first()
        
        if image is None:
            print(f"⚠️  No Landsat-8 images found for ({lat}, {lng})")
            return None
        
        print(f"🛰️  Found Landsat-8 image for ({lat}, {lng})")
        return image
        
    except Exception as e:
        print(f"❌ Error fetching Landsat-8 image: {e}")
        return None

def download_ee_image(image, point, scale=10, size=640, output_path=None):
    """
    Download Earth Engine image to local file.
    
    Args:
        image (ee.Image): Earth Engine image
        point (tuple): (lat, lng) coordinates
        scale (int): Resolution in meters (10m for Sentinel-2, 30m for Landsat-8)
        size (int): Image size in pixels
        output_path (str): Path to save image
        
    Returns:
        str or None: Path to downloaded image
    """
    if not EE_AVAILABLE or image is None:
        return None
    
    try:
        import requests
        from PIL import Image
        import io
        
        lat, lng = point
        region = ee.Geometry.Point([lng, lat]).buffer(size * scale / 2).bounds()
        
        # Get download URL
        url = image.getThumbURL({
            'region': region,
            'dimensions': f'{size}x{size}',
            'format': 'png'
        })
        
        # Download image
        response = requests.get(url)
        
        if response.status_code == 200:
            if output_path:
                with open(output_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Downloaded Earth Engine image to: {output_path}")
                return output_path
            else:
                return response.content
        else:
            print(f"❌ Failed to download image: HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error downloading Earth Engine image: {e}")
        return None

def get_satellite_image_ee(lat, lng, output_path, satellite='sentinel2'):
    """
    Unified function to get satellite imagery using Earth Engine.
    
    Args:
        lat (float): Latitude
        lng (float): Longitude
        output_path (str): Path to save image
        satellite (str): 'sentinel2' or 'landsat8'
        
    Returns:
        bool: True if successful
    """
    if not EE_AVAILABLE:
        print("❌ Earth Engine not available")
        return False
    
    # Initialize Earth Engine
    if not initialize_earth_engine():
        return False
    
    # Get image based on satellite type
    if satellite.lower() == 'sentinel2':
        image = get_sentinel2_image(lat, lng)
        scale = 10  # 10m resolution
    elif satellite.lower() == 'landsat8':
        image = get_landsat8_image(lat, lng)
        scale = 30  # 30m resolution
    else:
        print(f"❌ Unknown satellite type: {satellite}")
        return False
    
    if image is None:
        return False
    
    # Select RGB bands for visualization
    if satellite.lower() == 'sentinel2':
        vis_image = image.select(['B4', 'B3', 'B2'])  # RGB for Sentinel-2
    else:
        vis_image = image.select(['SR_B4', 'SR_B3', 'SR_B2'])  # RGB for Landsat-8
    
    # Download image
    result = download_ee_image(vis_image, (lat, lng), scale=scale, output_path=output_path)
    
    return result is not None

