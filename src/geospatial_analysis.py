import geopandas as gpd
from shapely.geometry import Polygon

def compare_areas(real_coords, registered_coords):
    """Compare actual land area with registered cadastral area."""
    real_polygon = Polygon(real_coords)
    registered_polygon = Polygon(registered_coords)
    real_area = real_polygon.area
    registered_area = registered_polygon.area
    difference = abs(real_area - registered_area)
    return {
        "real_area": real_area,
        "registered_area": registered_area,
        "difference": difference,
        "percent_difference": (difference / registered_area) * 100 if registered_area else 0
    }
