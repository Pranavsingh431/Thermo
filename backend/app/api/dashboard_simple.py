"""
Simple dashboard API for testing
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/test")
async def test_endpoint():
    """Simple test endpoint"""
    return {"status": "dashboard_working", "message": "Simple dashboard test successful"}

@router.get("/health")
async def dashboard_health():
    """Dashboard health check"""
    return {"status": "healthy", "service": "dashboard"} 