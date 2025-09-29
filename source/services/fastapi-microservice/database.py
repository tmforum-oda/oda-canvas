"""
Database configuration and session management.
Uses SQLite as embedded database for simplicity.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os

# SQLite database URL (embedded database)
DATABASE_URL = "sqlite:///./microservice.db"

# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
def init_db():
    """Initialize database with tables"""
    create_tables()
    print("Database initialized successfully!")