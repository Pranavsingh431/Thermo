"""
Dashboard API routes for thermal analysis results
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, desc
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.thermal_scan import ThermalScan
from app.models.ai_analysis import AIAnalysis, Detection
from app.models.substation import Substation
from app.utils.auth import get_current_user

router = APIRouter()

# Pydantic models for responses
class DashboardStats(BaseModel):
    total_images_processed: int
    images_today: int
    critical_issues: int
    total_substations: int
    active_batches: int
    last_processed: Optional[str]

class RecentAnalysis(BaseModel):
    id: int
    filename: str
    substation_name: Optional[str]
    risk_level: str
    critical_hotspots: int
    potential_hotspots: int
    processed_at: str
    quality_score: float
    # Additional fields for frontend
    ai_model: str
    processing_time: float
    components_detected: int
    max_temp: float
    analysis_status: str

class SubstationSummary(BaseModel):
    id: int
    name: str
    code: str
    total_scans: int
    critical_count: int
    potential_count: int
    last_scan: Optional[str]
    avg_quality_score: Optional[float]

class ThermalScanDetail(BaseModel):
    id: int
    filename: str
    capture_timestamp: str
    processing_status: str
    substation_name: Optional[str]
    latitude: Optional[float]
    longitude: Optional[float]
    file_size: str
    quality_score: Optional[float]
    risk_level: Optional[str]
    critical_hotspots: Optional[int]
    total_components: Optional[int]
    max_temperature: Optional[float]

class DetectionDetail(BaseModel):
    id: int
    component_type: str
    confidence: float
    hotspot_classification: str
    max_temperature: Optional[float]
    risk_level: Optional[str]
    bbox: dict

@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get overall dashboard statistics"""
    
    today = datetime.now().date()
    
    # Total images processed
    total_query = db.query(ThermalScan)
    if not current_user.can_view_all_data:
        total_query = total_query.filter(ThermalScan.uploaded_by == current_user.id)
    
    total_images = total_query.count()
    
    # Images processed today
    images_today = total_query.filter(
        func.date(ThermalScan.created_at) == today
    ).count()
    
    # Critical issues
    critical_issues = db.query(AIAnalysis).join(ThermalScan).filter(
        AIAnalysis.requires_immediate_attention == True
    )
    if not current_user.can_view_all_data:
        critical_issues = critical_issues.filter(ThermalScan.uploaded_by == current_user.id)
    critical_count = critical_issues.count()
    
    # Total substations
    total_substations = db.query(Substation).filter(Substation.is_active == True).count()
    
    # Active batches (processing or pending)
    active_batches = total_query.filter(
        ThermalScan.processing_status.in_(["pending", "processing"])
    ).with_entities(ThermalScan.batch_id).distinct().count()
    
    # Last processed
    last_scan = total_query.filter(
        ThermalScan.processing_status == "completed"
    ).order_by(desc(ThermalScan.processing_completed_at)).first()
    
    last_processed = None
    if last_scan and last_scan.processing_completed_at:
        last_processed = last_scan.processing_completed_at.isoformat()
    
    return DashboardStats(
        total_images_processed=total_images,
        images_today=images_today,
        critical_issues=critical_count,
        total_substations=total_substations,
        active_batches=active_batches,
        last_processed=last_processed
    )

@router.get("/recent-analyses", response_model=List[RecentAnalysis])
async def get_recent_analyses(
    limit: int = Query(default=10, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get recent thermal analyses"""
    
    query = db.query(AIAnalysis).join(ThermalScan).options(
        joinedload(AIAnalysis.thermal_scan).joinedload(ThermalScan.substation)
    )
    
    if not current_user.can_view_all_data:
        query = query.filter(ThermalScan.uploaded_by == current_user.id)
    
    analyses = query.filter(
        AIAnalysis.analysis_status == "completed"
    ).order_by(desc(AIAnalysis.created_at)).limit(limit).all()
    
    results = []
    for analysis in analyses:
        substation_name = None
        if analysis.thermal_scan.substation:
            substation_name = analysis.thermal_scan.substation.name
        
        results.append(RecentAnalysis(
            id=analysis.id,
            filename=analysis.thermal_scan.original_filename,
            substation_name=substation_name,
            risk_level=analysis.overall_risk_level or "unknown",
            critical_hotspots=analysis.critical_hotspots or 0,
            potential_hotspots=analysis.potential_hotspots or 0,
            processed_at=analysis.created_at.isoformat(),
            quality_score=analysis.quality_score or 0.0,
            # Additional fields for frontend
            ai_model=analysis.model_version or "AI Pipeline",
            processing_time=analysis.processing_duration_seconds or 0.0,
            components_detected=analysis.total_components_detected or 0,
            max_temp=analysis.max_temperature_detected or 0.0,
            analysis_status=analysis.analysis_status or "completed"
        ))
    
    return results

@router.get("/substations", response_model=List[SubstationSummary])
async def get_substation_summaries(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary statistics for all substations"""
    
    substations = db.query(Substation).filter(Substation.is_active == True).all()
    
    results = []
    for substation in substations:
        # Get scan statistics for this substation
        scan_query = db.query(ThermalScan).filter(ThermalScan.substation_id == substation.id)
        
        if not current_user.can_view_all_data:
            scan_query = scan_query.filter(ThermalScan.uploaded_by == current_user.id)
        
        total_scans = scan_query.count()
        
        # Get critical and potential counts
        analysis_query = db.query(AIAnalysis).join(ThermalScan).filter(
            ThermalScan.substation_id == substation.id
        )
        if not current_user.can_view_all_data:
            analysis_query = analysis_query.filter(ThermalScan.uploaded_by == current_user.id)
        
        critical_count = analysis_query.filter(AIAnalysis.critical_hotspots > 0).count()
        potential_count = analysis_query.filter(AIAnalysis.potential_hotspots > 0).count()
        
        # Average quality score
        avg_quality = analysis_query.with_entities(func.avg(AIAnalysis.quality_score)).scalar()
        
        # Last scan
        last_scan = scan_query.order_by(desc(ThermalScan.created_at)).first()
        last_scan_time = None
        if last_scan:
            last_scan_time = last_scan.created_at.isoformat()
        
        results.append(SubstationSummary(
            id=substation.id,
            name=substation.name,
            code=substation.code,
            total_scans=total_scans,
            critical_count=critical_count,
            potential_count=potential_count,
            last_scan=last_scan_time,
            avg_quality_score=round(avg_quality, 2) if avg_quality else None
        ))
    
    return results

@router.get("/thermal-scans", response_model=List[ThermalScanDetail])
async def get_thermal_scans(
    substation_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(default=50, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get thermal scans with optional filtering"""
    
    query = db.query(ThermalScan).options(
        joinedload(ThermalScan.substation),
        joinedload(ThermalScan.ai_analysis)
    )
    
    if not current_user.can_view_all_data:
        query = query.filter(ThermalScan.uploaded_by == current_user.id)
    
    if substation_id:
        query = query.filter(ThermalScan.substation_id == substation_id)
    
    if status:
        query = query.filter(ThermalScan.processing_status == status)
    
    scans = query.order_by(desc(ThermalScan.created_at)).limit(limit).all()
    
    results = []
    for scan in scans:
        substation_name = scan.substation.name if scan.substation else None
        quality_score = None
        risk_level = None
        critical_hotspots = None
        total_components = None
        
        if scan.ai_analysis:
            quality_score = scan.ai_analysis.quality_score
            risk_level = scan.ai_analysis.overall_risk_level
            critical_hotspots = scan.ai_analysis.critical_hotspots
            total_components = scan.ai_analysis.total_components_detected
        
        max_temperature = None
        if scan.ai_analysis:
            max_temperature = scan.ai_analysis.max_temperature_detected
        
        results.append(ThermalScanDetail(
            id=scan.id,
            filename=scan.original_filename,
            capture_timestamp=scan.capture_timestamp.isoformat() if scan.capture_timestamp else "",
            processing_status=scan.processing_status,
            substation_name=substation_name,
            latitude=scan.latitude,
            longitude=scan.longitude,
            file_size=scan.file_size_str,
            quality_score=quality_score,
            risk_level=risk_level,
            critical_hotspots=critical_hotspots,
            total_components=total_components,
            max_temperature=max_temperature
        ))
    
    return results

@router.get("/analysis/{analysis_id}/detections", response_model=List[DetectionDetail])
async def get_analysis_detections(
    analysis_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed detections for a specific analysis"""
    
    # Check if analysis exists and user has access
    analysis = db.query(AIAnalysis).join(ThermalScan).filter(
        AIAnalysis.id == analysis_id
    ).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Analysis not found"
        )
    
    if not current_user.can_view_all_data and analysis.thermal_scan.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this analysis"
        )
    
    detections = db.query(Detection).filter(Detection.ai_analysis_id == analysis_id).all()
    
    results = []
    for detection in detections:
        results.append(DetectionDetail(
            id=detection.id,
            component_type=detection.component_type,
            confidence=detection.confidence,
            hotspot_classification=detection.hotspot_classification,
            max_temperature=detection.max_temperature,
            risk_level=detection.risk_level,
            bbox=detection.bbox_dict
        ))
    
    return results

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "dashboard"} 