from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pandas as pd
from datetime import datetime
import os

# Get the project root directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "iptu_data.db")

# Configure SQLite database (easier for development)
DB_URL = f"sqlite:///{DB_PATH}"
engine = create_engine(DB_URL, echo=False)

Base = declarative_base()

class LandRecord(Base):
    """Land record model for database."""
    __tablename__ = "land_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    address = Column(String, nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    registered_area = Column(Float, nullable=False)  # Area declared by owner (m²)
    real_area = Column(Float, nullable=False)  # Area measured from satellite (m²)
    difference = Column(Float)  # Absolute difference
    percent_difference = Column(Float)  # Percentage difference
    status = Column(String)  # "compliant", "underdeclared", "overdeclared"
    analyzed_date = Column(DateTime, default=datetime.now)

def init_database():
    """Initialize database and create tables."""
    Base.metadata.create_all(engine)
    print(f"✅ Database initialized at: {DB_PATH}")

def save_terrain_data(data):
    """Save land analysis data into the database."""
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        record = LandRecord(
            address=data.get("address"),
            latitude=data.get("latitude"),
            longitude=data.get("longitude"),
            registered_area=data.get("registered_area"),
            real_area=data.get("real_area"),
            difference=data.get("difference"),
            percent_difference=data.get("percent_difference"),
            status=data.get("status")
        )
        session.add(record)
        session.commit()
        print(f"✅ Saved: {data.get('address')}")
        return True
    except Exception as e:
        session.rollback()
        print(f"❌ Error saving data: {e}")
        return False
    finally:
        session.close()

def get_all_records():
    """Retrieve all land records from database."""
    query = "SELECT * FROM land_records"
    return pd.read_sql(query, engine)

def clear_database():
    """Clear all records from database (useful for testing)."""
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        session.query(LandRecord).delete()
        session.commit()
        print("✅ Database cleared")
    except Exception as e:
        session.rollback()
        print(f"❌ Error clearing database: {e}")
    finally:
        session.close()
