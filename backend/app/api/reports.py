"""
Reports API - Generate thermal inspection reports
"""

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.models.ai_analysis import AIAnalysis
from app.utils.auth import get_current_user, require_permission
from app.services.intelligent_report_generator import intelligent_report_generator
from app.utils.email import email_service

router = APIRouter()

class ReportRequest(BaseModel):
    analysis_id: int
    format: Optional[str] = "comprehensive"  # comprehensive, summary, technical, email
    include_pdf: Optional[bool] = False
    include_llm: Optional[bool] = False

class ReportResponse(BaseModel):
    report_id: str
    generation_timestamp: str
    formats_generated: list
    download_links: dict
    email_summary: Optional[str] = None

@router.post("/generate/{analysis_id}", response_model=Dict[str, Any])
async def generate_thermal_report(
    analysis_id: int,
    background_tasks: BackgroundTasks,
    format: str = "comprehensive",
    include_pdf: bool = False,
    include_llm: bool = False,
    current_user: User = Depends(require_permission("view_reports")),
    db: Session = Depends(get_db)
):
    """Generate a thermal inspection report for the specified analysis"""
    
    try:
        # Get the AI analysis record
        analysis = db.query(AIAnalysis).filter(AIAnalysis.id == analysis_id).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI Analysis with ID {analysis_id} not found"
            )
        
        # Check user permissions
        if not current_user.can_view_all_data:
            # Check if user has access to this analysis
            if analysis.thermal_scan.uploaded_by != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this analysis"
                )
        
        # Generate the comprehensive report
        report_data = await intelligent_report_generator.generate_comprehensive_report(
            analysis=analysis,
            db=db
        )
        
        if 'error' in report_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Report generation failed: {report_data['error']}"
            )
        
        # Prepare response
        response_data = {
            'success': True,
            'report_id': report_data['report_id'],
            'generation_timestamp': report_data['generation_timestamp'],
            'formats_generated': report_data['formats_generated'],
            'analysis_id': analysis_id,
            'scan_filename': analysis.thermal_scan.original_filename,
            'risk_level': analysis.overall_risk_level,
            'critical_hotspots': analysis.critical_hotspots,
            'download_links': {}
        }
        
        # Add format-specific data
        if 'json' in report_data['formats_generated']:
            response_data['json_report'] = report_data.get('json_report')
        
        if 'text' in report_data['formats_generated']:
            response_data['professional_summary'] = report_data.get('professional_summary')
        
        if 'technical' in report_data['formats_generated']:
            response_data['technical_analysis'] = report_data.get('technical_analysis')
        
        if 'email' in report_data['formats_generated']:
            response_data['email_summary'] = report_data.get('email_summary')
        
        if 'pdf' in report_data['formats_generated']:
            response_data['pdf_path'] = report_data.get('pdf_path')
            response_data['download_links']['pdf'] = f"/api/reports/download/{report_data['report_id']}.pdf"
        
        if 'llm' in report_data['formats_generated']:
            response_data['llm_enhanced_summary'] = report_data.get('llm_enhanced_summary')
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error during report generation: {str(e)}"
        )

@router.get("/summary/{analysis_id}")
async def get_quick_summary(
    analysis_id: int,
    current_user: User = Depends(require_permission("view_reports")),
    db: Session = Depends(get_db)
):
    """Get a quick summary report for the specified analysis"""
    
    try:
        # Get the AI analysis record
        analysis = db.query(AIAnalysis).filter(AIAnalysis.id == analysis_id).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI Analysis with ID {analysis_id} not found"
            )
        
        # Check user permissions
        if not current_user.can_view_all_data:
            if analysis.thermal_scan.uploaded_by != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this analysis"
                )
        
        # Generate quick summary
        scan = analysis.thermal_scan
        substation = scan.substation if scan else None
        
        summary = {
            'analysis_id': analysis_id,
            'scan_filename': scan.original_filename,
            'capture_time': scan.capture_timestamp.isoformat() if scan.capture_timestamp else None,
            'substation': substation.name if substation else None,
            'risk_level': analysis.overall_risk_level,
            'risk_score': analysis.risk_score,
            'max_temperature': analysis.max_temperature_detected,
            'critical_hotspots': analysis.critical_hotspots,
            'potential_hotspots': analysis.potential_hotspots,
            'total_components': analysis.total_components_detected,
            'quality_score': analysis.quality_score,
            'requires_immediate_attention': analysis.requires_immediate_attention,
            'summary_text': analysis.summary_text,
            'model_version': analysis.model_version,
            'processing_time': analysis.processing_duration_seconds
        }
        
        return {
            'success': True,
            'summary': summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate summary: {str(e)}"
        )

@router.get("/batch-summary/{batch_id}")
async def get_batch_summary(
    batch_id: str,
    current_user: User = Depends(require_permission("view_reports")),
    db: Session = Depends(get_db)
):
    """Get a summary report for all analyses in a batch"""
    
    try:
        # Get all analyses for this batch
        from app.models.thermal_scan import ThermalScan
        
        query = db.query(AIAnalysis).join(ThermalScan).filter(
            ThermalScan.batch_id == batch_id
        )
        
        if not current_user.can_view_all_data:
            query = query.filter(ThermalScan.uploaded_by == current_user.id)
        
        analyses = query.all()
        
        if not analyses:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No analyses found for batch {batch_id}"
            )
        
        # Calculate batch statistics
        total_images = len(analyses)
        critical_count = sum(1 for a in analyses if a.critical_hotspots > 0)
        potential_count = sum(1 for a in analyses if a.potential_hotspots > 0)
        good_quality_count = sum(1 for a in analyses if a.is_good_quality)
        
        max_temp_overall = max(a.max_temperature_detected for a in analyses)
        avg_quality = sum(a.quality_score for a in analyses) / total_images
        
        # Risk distribution
        risk_distribution = {}
        for analysis in analyses:
            risk = analysis.overall_risk_level
            risk_distribution[risk] = risk_distribution.get(risk, 0) + 1
        
        # Individual analysis summaries
        analysis_summaries = []
        for analysis in analyses:
            scan = analysis.thermal_scan
            analysis_summaries.append({
                'analysis_id': analysis.id,
                'filename': scan.original_filename,
                'risk_level': analysis.overall_risk_level,
                'critical_hotspots': analysis.critical_hotspots,
                'max_temperature': analysis.max_temperature_detected,
                'components_detected': analysis.total_components_detected,
                'quality_score': analysis.quality_score,
                'requires_attention': analysis.requires_immediate_attention
            })
        
        batch_summary = {
            'batch_id': batch_id,
            'total_images': total_images,
            'statistics': {
                'critical_issues': critical_count,
                'potential_issues': potential_count,
                'good_quality_images': good_quality_count,
                'max_temperature_overall': max_temp_overall,
                'average_quality_score': round(avg_quality, 2),
                'risk_distribution': risk_distribution
            },
            'overall_status': 'critical' if critical_count > 0 else ('warning' if potential_count > 0 else 'normal'),
            'individual_analyses': analysis_summaries
        }
        
        return {
            'success': True,
            'batch_summary': batch_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate batch summary: {str(e)}"
        )

@router.get("/export/{analysis_id}")
async def export_analysis_data(
    analysis_id: int,
    format: str = "json",  # json, csv, excel
    current_user: User = Depends(require_permission("export_data")),
    db: Session = Depends(get_db)
):
    """Export analysis data in various formats"""
    
    try:
        # Get the AI analysis record with all related data
        analysis = db.query(AIAnalysis).filter(AIAnalysis.id == analysis_id).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI Analysis with ID {analysis_id} not found"
            )
        
        # Check permissions
        if not current_user.can_view_all_data:
            if analysis.thermal_scan.uploaded_by != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this analysis"
                )
        
        # Generate export data
        scan = analysis.thermal_scan
        detections = analysis.detections
        
        export_data = {
            'analysis_metadata': {
                'analysis_id': analysis.id,
                'model_version': analysis.model_version,
                'processing_time': analysis.processing_duration_seconds,
                'analysis_timestamp': analysis.created_at.isoformat(),
                'quality_score': analysis.quality_score
            },
            'scan_metadata': {
                'filename': scan.original_filename,
                'capture_timestamp': scan.capture_timestamp.isoformat() if scan.capture_timestamp else None,
                'camera_model': scan.camera_model,
                'file_size': scan.file_size_bytes,
                'dimensions': f"{scan.image_width}x{scan.image_height}" if scan.image_width else None,
                'gps_coordinates': {
                    'latitude': scan.latitude,
                    'longitude': scan.longitude
                }
            },
            'thermal_analysis': {
                'ambient_temperature': analysis.ambient_temperature,
                'max_temperature': analysis.max_temperature_detected,
                'min_temperature': analysis.min_temperature_detected,
                'avg_temperature': analysis.avg_temperature,
                'temperature_variance': analysis.temperature_variance
            },
            'hotspot_analysis': {
                'total_hotspots': analysis.total_hotspots,
                'critical_hotspots': analysis.critical_hotspots,
                'potential_hotspots': analysis.potential_hotspots,
                'normal_zones': analysis.normal_zones
            },
            'component_analysis': {
                'total_components': analysis.total_components_detected,
                'nuts_bolts_count': analysis.nuts_bolts_count,
                'mid_span_joints_count': analysis.mid_span_joints_count,
                'polymer_insulators_count': analysis.polymer_insulators_count
            },
            'risk_assessment': {
                'overall_risk_level': analysis.overall_risk_level,
                'risk_score': analysis.risk_score,
                'requires_immediate_attention': analysis.requires_immediate_attention,
                'recommendations': analysis.recommendations
            },
            'detailed_detections': []
        }
        
        # Add detailed detection data
        for detection in detections:
            detection_data = {
                'detection_id': detection.id,
                'component_type': detection.component_type,
                'confidence': detection.confidence,
                'bounding_box': detection.bbox_dict,
                'center_point': detection.center_point,
                'max_temperature': detection.max_temperature,
                'avg_temperature': detection.avg_temperature,
                'hotspot_classification': detection.hotspot_classification,
                'risk_level': detection.risk_level,
                'area_pixels': detection.area_pixels
            }
            export_data['detailed_detections'].append(detection_data)
        
        return {
            'success': True,
            'format': format,
            'export_data': export_data,
            'export_timestamp': analysis.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export analysis data: {str(e)}"
        )

@router.post("/email/{analysis_id}")
async def send_analysis_email(
    analysis_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("send_reports")),
    db: Session = Depends(get_db)
):
    """Send thermal analysis report via email"""
    
    try:
        # Get the AI analysis record
        analysis = db.query(AIAnalysis).filter(AIAnalysis.id == analysis_id).first()
        
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AI Analysis with ID {analysis_id} not found"
            )
        
        # Check user permissions
        if not current_user.can_view_all_data:
            if analysis.thermal_scan.uploaded_by != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this analysis"
                )
        
        # Prepare analysis results for email
        scan = analysis.thermal_scan
        analysis_results = {
            'good_quality_count': 1 if analysis.is_good_quality else 0,
            'poor_quality_count': 0 if analysis.is_good_quality else 1,
            'total_components': analysis.total_components_detected,
            'total_hotspots': analysis.total_hotspots,
            'critical_count': 1 if analysis.critical_hotspots > 0 else 0,
            'potential_count': 1 if analysis.potential_hotspots > 0 else 0,
            'normal_count': 1 if analysis.critical_hotspots == 0 and analysis.potential_hotspots == 0 else 0
        }
        
        batch_summary = {
            'total_images': 1,
            'processing_duration': f"{analysis.processing_duration_seconds:.2f}s",
            'substation_name': scan.substation.name if scan.substation else 'Unknown',
            'batch_id': scan.batch_id or f"SINGLE_{analysis_id}"
        }
        
        # Prepare critical alerts
        critical_alerts = []
        if analysis.critical_hotspots > 0:
            critical_alerts.append({
                'component_type': 'Critical Component',
                'max_temperature': analysis.max_temperature_detected,
                'location': f"{scan.latitude}, {scan.longitude}" if scan.latitude else 'Unknown',
                'confidence': analysis.quality_score,
                'risk_level': analysis.overall_risk_level
            })
        
        background_tasks.add_task(
            email_service.send_thermal_analysis_report,
            analysis_results,
            batch_summary,
            critical_alerts
        )
        
        return {
            'success': True,
            'message': 'Email report queued for sending',
            'analysis_id': analysis_id,
            'recipient': 'Chief Engineer (configured in settings)'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email report: {str(e)}"
        )

@router.post("/email/batch/{batch_id}")
async def send_batch_email(
    batch_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_permission("send_reports")),
    db: Session = Depends(get_db)
):
    """Send batch thermal analysis report via email"""
    
    try:
        # Get all analyses for this batch
        from app.models.thermal_scan import ThermalScan
        
        query = db.query(AIAnalysis).join(ThermalScan).filter(
            ThermalScan.batch_id == batch_id
        )
        
        if not current_user.can_view_all_data:
            query = query.filter(ThermalScan.uploaded_by == current_user.id)
        
        analyses = query.all()
        
        if not analyses:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No analyses found for batch {batch_id}"
            )
        
        # Calculate batch statistics
        total_images = len(analyses)
        critical_count = sum(1 for a in analyses if a.critical_hotspots > 0)
        potential_count = sum(1 for a in analyses if a.potential_hotspots > 0)
        good_quality_count = sum(1 for a in analyses if a.is_good_quality)
        total_processing_time = sum(a.processing_duration_seconds for a in analyses)
        
        analysis_results = {
            'good_quality_count': good_quality_count,
            'poor_quality_count': total_images - good_quality_count,
            'total_components': sum(a.total_components_detected for a in analyses),
            'total_hotspots': sum(a.total_hotspots for a in analyses),
            'critical_count': critical_count,
            'potential_count': potential_count,
            'normal_count': total_images - critical_count - potential_count
        }
        
        first_scan = analyses[0].thermal_scan
        batch_summary = {
            'total_images': total_images,
            'processing_duration': f"{total_processing_time:.2f}s",
            'substation_name': first_scan.substation.name if first_scan.substation else 'Unknown',
            'batch_id': batch_id
        }
        
        # Prepare critical alerts from all analyses
        critical_alerts = []
        for analysis in analyses:
            if analysis.critical_hotspots > 0:
                scan = analysis.thermal_scan
                critical_alerts.append({
                    'component_type': f'Critical in {scan.original_filename}',
                    'max_temperature': analysis.max_temperature_detected,
                    'location': f"{scan.latitude}, {scan.longitude}" if scan.latitude else 'Unknown',
                    'confidence': analysis.quality_score,
                    'risk_level': analysis.overall_risk_level
                })
        
        background_tasks.add_task(
            email_service.send_thermal_analysis_report,
            analysis_results,
            batch_summary,
            critical_alerts
        )
        
        return {
            'success': True,
            'message': 'Batch email report queued for sending',
            'batch_id': batch_id,
            'total_analyses': total_images,
            'critical_issues': critical_count,
            'recipient': 'Chief Engineer (configured in settings)'
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send batch email report: {str(e)}"
        )

@router.get("/health")
async def health_check():
    """Health check endpoint for reports service"""
    return {
        "status": "healthy",
        "service": "reports",
        "capabilities": [
            "comprehensive_reports",
            "professional_summaries", 
            "technical_analysis",
            "batch_summaries",
            "data_export",
            "email_reports"
        ]
    }   