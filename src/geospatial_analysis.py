import geopandas as gpd
from shapely.geometry import Polygon, Point
import numpy as np

def compare_areas(real_coords, registered_coords):
    """
    Compare actual land area with registered cadastral area using polygon geometries.
    
    Args:
        real_coords (list): List of (x, y) coordinates for real land boundary
        registered_coords (list): List of (x, y) coordinates for registered boundary
        
    Returns:
        dict: Analysis results including areas and differences
    """
    real_polygon = Polygon(real_coords)
    registered_polygon = Polygon(registered_coords)
    
    real_area = real_polygon.area
    registered_area = registered_polygon.area
    difference = abs(real_area - registered_area)
    
    # Calculate overlap
    intersection = real_polygon.intersection(registered_polygon)
    overlap_area = intersection.area
    overlap_percent = (overlap_area / registered_area) * 100 if registered_area else 0
    
    return {
        "real_area": real_area,
        "registered_area": registered_area,
        "difference": difference,
        "percent_difference": (difference / registered_area) * 100 if registered_area else 0,
        "overlap_area": overlap_area,
        "overlap_percent": overlap_percent
    }

def determine_status(real_area, registered_area, tolerance=5.0):
    """
    Determine compliance status based on area comparison.
    
    Args:
        real_area (float): Measured area from satellite (m²)
        registered_area (float): Declared area by owner (m²)
        tolerance (float): Acceptable deviation percentage (default: 5%)
        
    Returns:
        str: Status - "compliant", "underdeclared", or "overdeclared"
    """
    if registered_area == 0:
        return "error"
    
    difference = real_area - registered_area
    percent_difference = (difference / registered_area) * 100
    
    if abs(percent_difference) <= tolerance:
        return "compliant"
    elif percent_difference > tolerance:
        return "underdeclared"  # Real area is larger - potential tax evasion
    else:
        return "overdeclared"   # Real area is smaller - overpaying taxes

def create_geopandas_dataframe(records):
    """
    Convert analysis records to a GeoDataFrame for spatial analysis.
    
    Args:
        records (list): List of property analysis dictionaries
        
    Returns:
        GeoDataFrame: Spatial dataframe with property locations
    """
    geometries = [Point(r['longitude'], r['latitude']) for r in records if r.get('latitude') and r.get('longitude')]
    gdf = gpd.GeoDataFrame(records, geometry=geometries, crs="EPSG:4326")
    return gdf

def calculate_spatial_statistics(gdf):
    """
    Calculate spatial statistics on analyzed properties.
    
    Args:
        gdf (GeoDataFrame): GeoDataFrame with property data
        
    Returns:
        dict: Statistical summary
    """
    stats = {
        "total_properties": len(gdf),
        "avg_difference_percent": gdf['percent_difference'].mean(),
        "median_difference_percent": gdf['percent_difference'].median(),
        "max_difference_percent": gdf['percent_difference'].max(),
        "min_difference_percent": gdf['percent_difference'].min(),
        "total_underdeclared": len(gdf[gdf['status'] == 'underdeclared']),
        "total_overdeclared": len(gdf[gdf['status'] == 'overdeclared']),
        "total_compliant": len(gdf[gdf['status'] == 'compliant']),
    }
    return stats
