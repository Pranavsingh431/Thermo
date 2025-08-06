"""
API routes package
"""

from fastapi import APIRouter
from . import auth, upload, dashboard

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(upload.router, prefix="/upload", tags=["upload"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])

# Add missing AI analysis endpoints
@api_router.get("/ai-analyses/{analysis_id}")
async def get_ai_analysis(analysis_id: int):
    from sqlalchemy.orm import Session
    from app.database import get_db
    from app.models.ai_analysis import AIAnalysis
    
    db = next(get_db())
    try:
        analysis = db.query(AIAnalysis).filter(AIAnalysis.id == analysis_id).first()
        if not analysis:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="AI analysis not found")
        
        return {
            "id": analysis.id,
            "model_version": analysis.model_version,
            "analysis_status": analysis.analysis_status,
            "total_components_detected": analysis.total_components_detected,
            "yolo_model_path": analysis.yolo_model_path,
            "processing_duration_seconds": analysis.processing_duration_seconds,
            "risk_level": analysis.overall_risk_level,
            "quality_score": analysis.quality_score,
            "summary": analysis.summary_text
        }
    finally:
        db.close()

@api_router.get("/detections")
async def get_detections(ai_analysis_id: int):
    from sqlalchemy.orm import Session
    from app.database import get_db
    from app.models.ai_analysis import Detection
    
    db = next(get_db())
    try:
        detections = db.query(Detection).filter(Detection.ai_analysis_id == ai_analysis_id).all()
        return [
            {
                "id": det.id,
                "component_type": det.component_type,
                "confidence": det.confidence,
                "bbox": [det.bbox_x, det.bbox_y, det.bbox_width, det.bbox_height],
                "hotspot_classification": det.hotspot_classification,
                "risk_level": det.risk_level
            }
            for det in detections
        ]
    finally:
        db.close() 