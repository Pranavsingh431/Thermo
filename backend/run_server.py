#!/usr/bin/env python3
"""
Server startup script for Thermal Inspection API
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

# Now import and run the application
if __name__ == "__main__":
    import uvicorn
    from app.main import app
    
    print("🚀 Starting Thermal Inspection System API...")
    print(f"📁 Backend directory: {backend_dir}")
    print(f"🐍 Python path: {sys.path[0]}")
    
    uvicorn.run(
        app,
        host="127.0.0.1",
        port=8000,
        log_level="info",
        reload=False
    ) 