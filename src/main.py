#!/usr/bin/env python3
"""
IPTU Checker - Main Pipeline
Executes the complete analysis pipeline for property tax verification
"""

import sys
import os
from data_processing import get_coordinates, get_sample_properties, get_satellite_image
from image_analysis import process_land_measurement
from geospatial_analysis import determine_status
from database import init_database, save_terrain_data, clear_database, get_all_records

# Create directory for satellite images
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "..", "satellite_images")
os.makedirs(IMAGES_DIR, exist_ok=True)

def analyze_property(property_data):
    """Analyze a single property through the complete pipeline."""
    address = property_data["address"]
    registered_area = property_data["registered_area"]
    
    print(f"\n{'='*60}")
    print(f"📍 Analyzing: {address}")
    print(f"{'='*60}")
    
    try:
        # Step 1: Get coordinates
        lat, lng = get_coordinates(address)
        if lat is None or lng is None:
            print("❌ Could not get coordinates. Skipping.")
            return False
        
        # Step 2: Download satellite image
        image_filename = f"property_{hash(address) % 10000}.png"
        image_path = os.path.join(IMAGES_DIR, image_filename)
        
        print(f"\n📥 Downloading satellite image...")
        # Try Earth Engine first (Sentinel-2), then Google Maps as fallback
        success = get_satellite_image(lat, lng, zoom=19, size="640x640", 
                                      output_path=image_path, source='sentinel2')
        
        if not success:
            print("⚠️  Sentinel-2 failed, trying Landsat-8...")
            success = get_satellite_image(lat, lng, zoom=19, size="640x640",
                                         output_path=image_path, source='landsat8')
        
        if not success:
            print("⚠️  Landsat-8 failed, trying Google Maps...")
            success = get_satellite_image(lat, lng, zoom=19, size="640x640",
                                         output_path=image_path, source='google')
        
        if not success:
            print("❌ Could not download satellite image from any source. Skipping.")
            return False
        
        # Step 3: Analyze satellite image to get real area
        real_area = process_land_measurement(address, registered_area, lat, lng, image_path)
        
        # Step 4: Compare areas and determine status
        difference = abs(real_area - registered_area)
        percent_difference = (difference / registered_area) * 100 if registered_area else 0
        status = determine_status(real_area, registered_area)
        
        # Step 5: Save to database
        data = {
            "address": address,
            "latitude": lat,
            "longitude": lng,
            "registered_area": registered_area,
            "real_area": real_area,
            "difference": round(difference, 2),
            "percent_difference": round(percent_difference, 2),
            "status": status
        }
        
        save_terrain_data(data)
        
        # Display results
        print(f"\n📊 ANALYSIS RESULTS:")
        print(f"   Status: {status.upper()}")
        print(f"   Difference: {difference:.2f} m² ({percent_difference:.1f}%)")
        
        if status == "underdeclared":
            print(f"   ⚠️  ALERT: Potential tax evasion detected!")
        elif status == "overdeclared":
            print(f"   💰 Owner may be overpaying taxes")
        else:
            print(f"   ✅ Property is compliant")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing property: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_analysis(clear_db=False, csv_file=None):
    """Run complete analysis pipeline on properties."""
    print("🚀 IPTU CHECKER - Property Tax Verification System")
    print("="*60)
    
    # Initialize database
    init_database()
    
    if clear_db:
        print("\n🗑️  Clearing existing database...")
        clear_database()
    
    # Get properties
    if csv_file:
        from data_processing import load_properties_from_csv
        properties = load_properties_from_csv(csv_file)
    else:
        properties = get_sample_properties()
    
    if not properties:
        print("❌ No properties to analyze")
        return
    
    print(f"\n📋 Found {len(properties)} properties to analyze\n")
    
    # Analyze each property
    success_count = 0
    for i, prop in enumerate(properties, 1):
        print(f"\n[{i}/{len(properties)}]", end=" ")
        if analyze_property(prop):
            success_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"✅ ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Successfully analyzed: {success_count}/{len(properties)} properties")
    
    # Display summary from database
    print(f"\n📊 DATABASE SUMMARY:")
    df = get_all_records()
    if not df.empty:
        print(f"   Total records: {len(df)}")
        print(f"   Compliant: {len(df[df['status'] == 'compliant'])}")
        print(f"   Underdeclared: {len(df[df['status'] == 'underdeclared'])}")
        print(f"   Overdeclared: {len(df[df['status'] == 'overdeclared'])}")
        print(f"\n   Average difference: {df['percent_difference'].mean():.1f}%")
    
    print(f"\n🌐 To view the dashboard, run:")
    print(f"   streamlit run src/app.py")
    print("="*60)

if __name__ == "__main__":
    # Parse arguments
    clear_db = "--clear" in sys.argv
    csv_file = None
    
    for arg in sys.argv[1:]:
        if arg.endswith('.csv'):
            csv_file = arg
    
    run_analysis(clear_db=clear_db, csv_file=csv_file)

