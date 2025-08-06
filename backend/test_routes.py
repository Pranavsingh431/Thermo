#!/usr/bin/env python3
"""
Test script to debug route registration
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi import FastAPI
from app.api import auth, upload, dashboard

# Create test app
app = FastAPI(title="Test App")

print("=== TESTING ROUTE REGISTRATION ===")

# Test individual router registration
print(f"Auth router routes: {len(auth.router.routes)}")
print(f"Upload router routes: {len(upload.router.routes)}")
print(f"Dashboard router routes: {len(dashboard.router.routes)}")

# Register routers
print("\n=== REGISTERING ROUTERS ===")
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
print("✅ Auth router registered")

app.include_router(upload.router, prefix="/api/upload", tags=["File Upload"])
print("✅ Upload router registered")

app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])
print("✅ Dashboard router registered")

print(f"\n=== FINAL APP ROUTES ===")
for route in app.routes:
    if hasattr(route, 'path'):
        methods = getattr(route, 'methods', ['UNKNOWN'])
        print(f"  {route.path} {list(methods)}")

print(f"\nTotal routes registered: {len([r for r in app.routes if hasattr(r, 'path')])}") 