"""
Configuration settings for the FastAPI microservice.
"""

import os
from typing import Optional

class Settings:
    """Application settings"""
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./microservice.db")
    
    # API settings
    API_TITLE: str = "E-Commerce Microservice"
    API_DESCRIPTION: str = "A comprehensive microservice for managing a ODA Component Registry"
    API_VERSION: str = "1.0.0"
    
    # Server settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Pagination defaults
    DEFAULT_PAGE_SIZE: int = 100
    MAX_PAGE_SIZE: int = 1000

# Create settings instance
settings = Settings()