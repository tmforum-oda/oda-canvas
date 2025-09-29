#!/usr/bin/env python3
"""
Startup script for the Component Registry Service.

This script starts the FastAPI application using uvicorn.
"""

import uvicorn
from main import app

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False
    )