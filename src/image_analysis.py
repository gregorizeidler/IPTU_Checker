import cv2
import numpy as np
import os

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("⚠️  Warning: ultralytics not installed. Install with: pip install ultralytics")

try:
    from tensorflow_analysis import segment_land_tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("⚠️  Warning: TensorFlow not available. Install with: pip install tensorflow")

def process_image_with_segmentation(image_path, lat, lng):
    """
    Process satellite images using computer vision to detect and measure land areas.
    Uses image segmentation to identify building/land boundaries.
    
    Args:
        image_path (str): Path to satellite image
        lat (float): Latitude (for calculating pixel-to-meter conversion)
        lng (float): Longitude
        
    Returns:
        float: Calculated area in square meters
    """
    print(f"🔬 Processing image: {image_path}")
    
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"Image not found: {image_path}")
    
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")
    
    height, width = img.shape[:2]
    print(f"   Image dimensions: {width}x{height}")
    
    # Calculate meters per pixel based on zoom level and latitude
    # At zoom 19, one pixel ≈ 0.298 meters at equator
    # Adjust for latitude: meters_per_pixel = base * cos(latitude)
    import math
    zoom = 19
    base_meters_per_pixel = 156543.03392 * math.cos(math.radians(lat)) / (2 ** zoom)
    print(f"   Scale: {base_meters_per_pixel:.3f} meters/pixel")
    
    # Convert to grayscale and apply edge detection
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply Gaussian blur to reduce noise
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Edge detection using Canny
    edges = cv2.Canny(blurred, 50, 150)
    
    # Find contours (building/land boundaries)
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("   ⚠️  No contours detected in image")
        return None
    
    # Find the largest contour (assumed to be the main land/building area)
    largest_contour = max(contours, key=cv2.contourArea)
    contour_area_pixels = cv2.contourArea(largest_contour)
    
    # Convert pixel area to square meters
    area_m2 = contour_area_pixels * (base_meters_per_pixel ** 2)
    
    print(f"   📐 Detected area: {area_m2:.2f} m²")
    
    # Save annotated image
    output_path = image_path.replace('.png', '_analyzed.png')
    annotated = img.copy()
    cv2.drawContours(annotated, [largest_contour], -1, (0, 255, 0), 2)
    cv2.imwrite(output_path, annotated)
    print(f"   💾 Saved annotated image: {output_path}")
    
    return round(area_m2, 2)

def process_image_with_yolo(image_path, lat, lng):
    """
    Process satellite images using YOLO object detection to identify structures.
    
    Args:
        image_path (str): Path to satellite image
        lat (float): Latitude
        lng (float): Longitude
        
    Returns:
        float: Calculated area in square meters
    """
    if not YOLO_AVAILABLE:
        raise ImportError(
            "YOLO is not available. Install with: pip install ultralytics\n"
            "Falling back to segmentation method..."
        )
    
    print(f"🤖 Analyzing image with YOLO: {image_path}")
    
    # Load YOLO model
    model = YOLO("yolov8n.pt")  # Will auto-download if not present
    
    img = cv2.imread(image_path)
    results = model(img)
    
    # Calculate meters per pixel
    import math
    zoom = 19
    base_meters_per_pixel = 156543.03392 * math.cos(math.radians(lat)) / (2 ** zoom)
    
    total_area_pixels = 0
    annotated = img.copy()
    
    for result in results:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
            
            # Draw bounding box
            cv2.rectangle(annotated, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            
            # Calculate area
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            area_pixels = width * height
            total_area_pixels += area_pixels
    
    # Convert to square meters
    area_m2 = total_area_pixels * (base_meters_per_pixel ** 2)
    
    # Save annotated image
    output_path = image_path.replace('.png', '_yolo_analyzed.png')
    cv2.imwrite(output_path, annotated)
    print(f"   📐 Detected area: {area_m2:.2f} m²")
    print(f"   💾 Saved annotated image: {output_path}")
    
    return round(area_m2, 2)

def process_land_measurement(address, registered_area, lat, lng, image_path=None, method='auto'):
    """
    Measure land area from satellite imagery using computer vision.
    
    Args:
        address (str): Property address
        registered_area (float): Owner-declared area in m²
        lat (float): Latitude
        lng (float): Longitude
        image_path (str): Path to pre-downloaded satellite image
        method (str): 'auto', 'opencv', 'yolo', or 'tensorflow'
        
    Returns:
        float: Measured area in square meters
    """
    print(f"\n🛰️  Analyzing satellite imagery for: {address}")
    print(f"   📏 Registered area: {registered_area} m²")
    
    if not image_path or not os.path.exists(image_path):
        raise ValueError(
            f"Satellite image required but not found: {image_path}\n"
            f"Download the image first using data_processing.get_satellite_image()"
        )
    
    real_area = None
    
    # Choose analysis method
    if method == 'tensorflow' and TF_AVAILABLE:
        print("   🤖 Using TensorFlow for analysis")
        real_area = segment_land_tf(image_path, lat=lat, lng=lng)
    elif method == 'yolo' and YOLO_AVAILABLE:
        print("   🎯 Using YOLO for analysis")
        real_area = process_image_with_yolo(image_path, lat, lng)
    elif method == 'opencv':
        print("   🔬 Using OpenCV for analysis")
        real_area = process_image_with_segmentation(image_path, lat, lng)
    elif method == 'auto':
        # Try methods in order of preference
        print("   🔄 Auto-selecting analysis method...")
        if YOLO_AVAILABLE:
            print("   🎯 Using YOLO")
            try:
                real_area = process_image_with_yolo(image_path, lat, lng)
            except Exception as e:
                print(f"   ⚠️  YOLO failed: {e}, trying TensorFlow...")
                real_area = None
        
        if real_area is None and TF_AVAILABLE:
            print("   🤖 Using TensorFlow")
            try:
                real_area = segment_land_tf(image_path, lat=lat, lng=lng)
            except Exception as e:
                print(f"   ⚠️  TensorFlow failed: {e}, trying OpenCV...")
                real_area = None
        
        if real_area is None:
            print("   🔬 Using OpenCV")
            real_area = process_image_with_segmentation(image_path, lat, lng)
    else:
        # Fallback to OpenCV
        print("   🔬 Using OpenCV (default)")
        real_area = process_image_with_segmentation(image_path, lat, lng)
    
    if real_area is None:
        raise ValueError("Could not analyze image - no area detected")
    
    print(f"   ✅ Measured area: {real_area} m²")
    
    return real_area
