from sqlalchemy import create_engine
import pandas as pd

# Configure PostgreSQL + PostGIS database
DB_URL = "postgresql://user:password@localhost:5432/iptu_db"
engine = create_engine(DB_URL)

def save_terrain_data(data):
    """Save land analysis data into the database."""
    df = pd.DataFrame([data])
    df.to_sql("land_records", engine, if_exists="append", index=False)
