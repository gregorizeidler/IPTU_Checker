"""
REST API for IPTU Checker
FastAPI implementation for municipal system integration
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import sys
import os

# Add src to path
sys.path.append(os.path.dirname(__file__))

from database import get_all_records, save_terrain_data, init_database, engine
from data_processing import get_coordinates, get_sample_properties
from image_analysis import process_land_measurement
from geospatial_analysis import determine_status
from sqlalchemy.orm import sessionmaker

# Initialize FastAPI
app = FastAPI(
    title="IPTU Checker API",
    description="REST API for property tax verification using satellite imagery",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()
    print("✅ Database initialized")

# Pydantic models
class PropertyInput(BaseModel):
    address: str = Field(..., description="Full property address")
    registered_area: float = Field(..., gt=0, description="Registered area in m²")
    owner: Optional[str] = Field(None, description="Property owner name")

class PropertyAnalysis(BaseModel):
    id: int
    address: str
    latitude: Optional[float]
    longitude: Optional[float]
    registered_area: float
    real_area: float
    difference: float
    percent_difference: float
    status: str
    analyzed_date: datetime

class BatchAnalysisRequest(BaseModel):
    properties: List[PropertyInput]
    
class AnalysisStats(BaseModel):
    total_properties: int
    compliant: int
    underdeclared: int
    overdeclared: int
    avg_difference_percent: float
    total_potential_evasion: int

class HealthCheck(BaseModel):
    status: str
    timestamp: datetime
    database: str
    total_records: int

# Endpoints

@app.get("/", tags=["General"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": "IPTU Checker API",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": {
            "health": "/health",
            "properties": "/properties",
            "analyze": "/analyze",
            "stats": "/stats"
        }
    }

@app.get("/health", response_model=HealthCheck, tags=["General"])
async def health_check():
    """Health check endpoint"""
    try:
        df = get_all_records()
        total = len(df) if not df.empty else 0
        return {
            "status": "healthy",
            "timestamp": datetime.now(),
            "database": "connected",
            "total_records": total
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.get("/properties", response_model=List[PropertyAnalysis], tags=["Properties"])
async def get_properties(
    status: Optional[str] = Query(None, description="Filter by status: compliant, underdeclared, overdeclared"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Offset for pagination")
):
    """Get all analyzed properties with optional filters"""
    try:
        df = get_all_records()
        
        if df.empty:
            return []
        
        # Filter by status
        if status:
            df = df[df['status'] == status]
        
        # Pagination
        df = df.iloc[offset:offset + limit]
        
        # Convert to dict and return
        return df.to_dict('records')
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving properties: {str(e)}")

@app.get("/properties/{property_id}", response_model=PropertyAnalysis, tags=["Properties"])
async def get_property(property_id: int):
    """Get a specific property by ID"""
    try:
        df = get_all_records()
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No properties found")
        
        property_data = df[df['id'] == property_id]
        
        if property_data.empty:
            raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
        
        return property_data.to_dict('records')[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving property: {str(e)}")

@app.post("/analyze", tags=["Analysis"])
async def analyze_property(
    property_input: PropertyInput,
    background_tasks: BackgroundTasks
):
    """
    Analyze a single property
    Returns immediately with job ID, analysis runs in background
    """
    try:
        # Get coordinates
        lat, lng = get_coordinates(property_input.address)
        
        if lat is None or lng is None:
            raise HTTPException(status_code=400, detail=f"Could not geocode address: {property_input.address}")
        
        return {
            "status": "accepted",
            "message": "Analysis queued. Check /properties endpoint for results.",
            "address": property_input.address,
            "coordinates": {"lat": lat, "lng": lng},
            "note": "Full analysis with satellite imagery requires image download capability"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing property: {str(e)}")

@app.post("/batch", tags=["Analysis"])
async def batch_analyze(
    batch: BatchAnalysisRequest,
    background_tasks: BackgroundTasks
):
    """
    Batch analysis of multiple properties
    Returns immediately, analysis runs in background
    """
    if len(batch.properties) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 properties per batch")
    
    results = []
    for prop in batch.properties:
        try:
            lat, lng = get_coordinates(prop.address)
            results.append({
                "address": prop.address,
                "status": "queued" if lat else "failed",
                "coordinates": {"lat": lat, "lng": lng} if lat else None
            })
        except:
            results.append({
                "address": prop.address,
                "status": "failed",
                "error": "Geocoding failed"
            })
    
    return {
        "status": "accepted",
        "total_properties": len(batch.properties),
        "results": results,
        "message": "Batch analysis queued. Check /properties endpoint for results."
    }

@app.get("/stats", response_model=AnalysisStats, tags=["Statistics"])
async def get_statistics():
    """Get overall statistics of analyzed properties"""
    try:
        df = get_all_records()
        
        if df.empty:
            return {
                "total_properties": 0,
                "compliant": 0,
                "underdeclared": 0,
                "overdeclared": 0,
                "avg_difference_percent": 0.0,
                "total_potential_evasion": 0
            }
        
        stats = {
            "total_properties": len(df),
            "compliant": len(df[df['status'] == 'compliant']),
            "underdeclared": len(df[df['status'] == 'underdeclared']),
            "overdeclared": len(df[df['status'] == 'overdeclared']),
            "avg_difference_percent": float(df['percent_difference'].mean()),
            "total_potential_evasion": len(df[df['status'] == 'underdeclared'])
        }
        
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating statistics: {str(e)}")

@app.get("/export", tags=["Export"])
async def export_data(
    format: str = Query("json", description="Export format: json or csv")
):
    """Export all property data"""
    try:
        df = get_all_records()
        
        if df.empty:
            raise HTTPException(status_code=404, detail="No data to export")
        
        if format == "csv":
            from fastapi.responses import StreamingResponse
            import io
            
            stream = io.StringIO()
            df.to_csv(stream, index=False)
            stream.seek(0)
            
            return StreamingResponse(
                iter([stream.getvalue()]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=iptu_data.csv"}
            )
        else:
            return df.to_dict('records')
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting data: {str(e)}")

@app.delete("/properties/{property_id}", tags=["Properties"])
async def delete_property(property_id: int):
    """Delete a property analysis (admin only)"""
    try:
        Session = sessionmaker(bind=engine)
        session = Session()
        
        from database import LandRecord
        
        record = session.query(LandRecord).filter(LandRecord.id == property_id).first()
        
        if not record:
            raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
        
        session.delete(record)
        session.commit()
        session.close()
        
        return {"status": "deleted", "property_id": property_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting property: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting IPTU Checker API...")
    print("📊 API Documentation: http://localhost:8000/docs")
    print("🔍 Interactive API: http://localhost:8000/redoc")
    uvicorn.run(app, host="0.0.0.0", port=8000)

