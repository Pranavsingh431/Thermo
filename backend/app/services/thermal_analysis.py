"""
Thermal analysis background processing service - Full AI Pipeline Integration
"""

import asyncio
import logging
from typing import List
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import SessionLocal
from app.models.thermal_scan import ThermalScan
from app.models.ai_analysis import AIAnalysis, Detection
from app.models.substation import Substation
from app.utils.thermal_processing import thermal_processor
from app.utils.email import email_service

# Import Enhanced AI Pipeline
try:
    from app.services.enhanced_ai_pipeline import enhanced_thermal_analyzer
    from app.services.full_ai_pipeline import create_full_ai_system
    ENHANCED_AI_AVAILABLE = True
    FULL_AI_AVAILABLE = True
    print("🚀 Using ENHANCED AI Pipeline - Real FLIR + YOLO-NAS + Advanced Analysis")
except ImportError:
    try:
        from app.services.full_ai_pipeline import create_full_ai_system
        ENHANCED_AI_AVAILABLE = False
        FULL_AI_AVAILABLE = True
        print("🚀 Using FULL AI Pipeline - YOLO-NAS + CNN + Advanced Thermal Analysis")
    except ImportError:
        from app.services.ai_pipeline import thermal_analyzer
        ENHANCED_AI_AVAILABLE = False
        FULL_AI_AVAILABLE = False
        print("⚠️ Using Lightweight AI Pipeline")

logger = logging.getLogger(__name__)

async def process_thermal_batch(batch_id: str, db: Session, user_id: int):
    """Process a batch of thermal images using ENHANCED AI pipeline"""
    pipeline_name = "ENHANCED AI" if ENHANCED_AI_AVAILABLE else ("FULL AI" if FULL_AI_AVAILABLE else "Lightweight AI")
    logger.info(f"🚀 Starting {pipeline_name}-powered processing for batch {batch_id}")
    
    try:
        # Get all thermal scans in this batch
        scans = db.query(ThermalScan).filter(
            ThermalScan.batch_id == batch_id,
            ThermalScan.processing_status == "pending"
        ).all()
        
        if not scans:
            logger.warning(f"No pending scans found for batch {batch_id}")
            return
        
        batch_results = {
            'total_images': len(scans),
            'processed_count': 0,
            'failed_count': 0,
            'good_quality_count': 0,
            'poor_quality_count': 0,
            'total_components': 0,
            'total_hotspots': 0,
            'critical_count': 0,
            'potential_count': 0,
            'normal_count': 0,
            'defects_detected': 0,
            'ai_models_used': []
        }
        
        critical_alerts = []
        substation_name = "Unknown"
        
        # Initialize FULL AI System
        if FULL_AI_AVAILABLE:
            ai_system = create_full_ai_system()
            batch_results['ai_models_used'] = ['YOLO-NAS-S', 'EfficientNet-B0', 'Advanced Thermal Analysis']
        else:
            ai_system = None
            batch_results['ai_models_used'] = ['Lightweight Thermal Analysis']
        
        # Process each scan with FULL AI pipeline
        for scan in scans:
            try:
                logger.info(f"🤖 Processing {scan.original_filename} with FULL AI pipeline...")
                
                # Update processing status
                scan.update_processing_status("processing")
                db.commit()
                
                # Run FULL AI analysis
                ai_result = await process_single_thermal_image_full_ai(scan, db, ai_system)
                
                if ai_result:
                    batch_results['processed_count'] += 1
                    
                    # Update counters based on FULL AI results
                    if ai_result.is_good_quality:
                        batch_results['good_quality_count'] += 1
                    else:
                        batch_results['poor_quality_count'] += 1
                    
                    batch_results['total_components'] += ai_result.total_components_detected or 0
                    batch_results['total_hotspots'] += ai_result.total_hotspots or 0
                    
                    if ai_result.overall_risk_level == "critical":
                        batch_results['critical_count'] += 1
                        critical_alerts.append({
                            'filename': scan.original_filename,
                            'risk_score': ai_result.risk_score,
                            'critical_hotspots': ai_result.critical_hotspots,
                            'summary': ai_result.summary_text,
                            'defects': getattr(ai_result, 'defects_summary', 'Multiple defects detected'),
                            'max_temperature': ai_result.max_temperature_detected
                        })
                    elif ai_result.overall_risk_level == "medium":
                        batch_results['potential_count'] += 1
                    else:
                        batch_results['normal_count'] += 1
                    
                    # Count defects detected
                    detections = db.query(Detection).filter(Detection.ai_analysis_id == ai_result.id).all()
                    defective_detections = [d for d in detections if d.hotspot_classification != 'normal']
                    batch_results['defects_detected'] += len(defective_detections)
                    
                    # Get substation name for reporting
                    if scan.substation:
                        substation_name = scan.substation.name
                    
                    # Mark as completed
                    scan.update_processing_status("completed")
                    
                else:
                    batch_results['failed_count'] += 1
                    scan.update_processing_status("failed")
                
            except Exception as e:
                logger.error(f"Failed to process {scan.original_filename}: {e}")
                batch_results['failed_count'] += 1
                scan.update_processing_status("failed")
            
            db.commit()
        
        # Send email notification if critical issues found
        if critical_alerts:
            try:
                await email_service.send_thermal_analysis_report(
                    critical_alerts=critical_alerts,
                    batch_summary=batch_results,
                    substation_name=substation_name
                )
                logger.info(f"📧 Critical alert email sent for {len(critical_alerts)} issues")
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")
        
        logger.info(f"✅ FULL AI Batch {batch_id} completed: {batch_results}")
        
    except Exception as e:
        logger.error(f"❌ FULL AI Batch processing failed for {batch_id}: {e}")

async def process_single_thermal_image_full_ai(scan: ThermalScan, db: Session, ai_system=None) -> AIAnalysis:
    """Process a single thermal image using FULL AI pipeline"""
    try:
        # Check if AI analysis already exists
        existing_analysis = db.query(AIAnalysis).filter(AIAnalysis.thermal_scan_id == scan.id).first()
        if existing_analysis:
            logger.info(f"✅ AI analysis already exists for {scan.original_filename}, returning existing result")
            return existing_analysis
        
        logger.info(f"🧠 Running ENHANCED AI analysis on {scan.original_filename}...")
        
        if ENHANCED_AI_AVAILABLE:
            # Use the new enhanced AI pipeline with real FLIR extraction
            enhanced_result = enhanced_thermal_analyzer.analyze_image(
                image_path=scan.file_path,
                image_id=str(scan.id),
                ambient_temp=scan.ambient_temperature
            )
            
            # Convert enhanced result to expected format
            ai_result = {
                'max_temperature': enhanced_result.max_temperature,
                'min_temperature': enhanced_result.min_temperature,
                'avg_temperature': enhanced_result.avg_temperature,
                'temperature_variance': enhanced_result.temperature_variance,
                'total_hotspots': enhanced_result.total_hotspots,
                'critical_hotspots': enhanced_result.critical_hotspots,
                'potential_hotspots': enhanced_result.potential_hotspots,
                'normal_zones': enhanced_result.normal_zones,
                'quality_score': enhanced_result.quality_score,
                'is_good_quality': enhanced_result.is_good_quality,
                'overall_risk_level': enhanced_result.overall_risk_level,
                'risk_score': enhanced_result.risk_score,
                'requires_immediate_attention': enhanced_result.requires_immediate_attention,
                'summary_text': enhanced_result.summary_text,
                'processing_time': enhanced_result.processing_time,
                'total_components': enhanced_result.total_components,
                'components': enhanced_result.detections,
                'model_version': enhanced_result.model_version,
                'yolo_model_used': enhanced_result.yolo_model_used,
                'thermal_extraction_method': enhanced_result.thermal_extraction_method,
                'camera_model': enhanced_result.camera_model,
                'gps_data': enhanced_result.gps_data,
                'thermal_calibration_used': enhanced_result.thermal_calibration_used
            }
            
            components = enhanced_result.detections
            component_summary = {
                'nuts_bolts_count': enhanced_result.nuts_bolts_count,
                'mid_span_joints_count': enhanced_result.mid_span_joints_count,
                'polymer_insulators_count': enhanced_result.polymer_insulators_count,
                'conductor_count': enhanced_result.conductor_count,
                'total_components': enhanced_result.total_components
            }
            detailed_analysis = {
                'thermal_calibration_used': enhanced_result.thermal_calibration_used,
                'camera_model': enhanced_result.camera_model,
                'model_version': enhanced_result.model_version
            }
            
        elif FULL_AI_AVAILABLE and ai_system:
            # Run FULL AI analysis as fallback
            ai_result = ai_system.analyze_image(
                image_path=scan.file_path,
                image_id=str(scan.id)
            )
            
            # Extract results from full AI system
            components = ai_result.get('components', [])
            component_summary = ai_result.get('component_summary', {})
            detailed_analysis = ai_result.get('detailed_analysis', {})
            
        else:
            # Fallback to lightweight analysis
            from app.services.ai_pipeline import thermal_analyzer
            lightweight_result = thermal_analyzer.analyze_image(
                image_path=scan.file_path,
                image_id=str(scan.id)
            )
            
            # Convert lightweight result to full AI format
            ai_result = {
                'max_temperature': lightweight_result.max_temperature,
                'min_temperature': lightweight_result.min_temperature,
                'avg_temperature': lightweight_result.avg_temperature,
                'total_hotspots': lightweight_result.total_hotspots,
                'critical_hotspots': lightweight_result.critical_hotspots,
                'potential_hotspots': lightweight_result.potential_hotspots,
                'quality_score': lightweight_result.quality_score,
                'is_good_quality': lightweight_result.is_good_quality,
                'overall_risk_level': lightweight_result.overall_risk_level,
                'risk_score': lightweight_result.risk_score,
                'requires_immediate_attention': lightweight_result.requires_immediate_attention,
                'summary_text': lightweight_result.summary_text,
                'processing_time': lightweight_result.processing_time,
                'total_components': lightweight_result.total_components,
                'components': lightweight_result.detections
            }
            
            component_summary = {
                'nuts_bolts': lightweight_result.nuts_bolts_count,
                'mid_span_joints': lightweight_result.mid_span_joints_count,
                'polymer_insulators': lightweight_result.polymer_insulators_count,
                'defects_found': 0,
                'normal_components': lightweight_result.total_components
            }
            
            components = []
        
        logger.info(f"🎯 AI analysis completed: Risk={ai_result['overall_risk_level']}, "
                   f"Quality={ai_result['quality_score']:.2f}, "
                   f"Hotspots={ai_result['total_hotspots']}, "
                   f"Components={ai_result.get('total_components', 0)}")
        
        # Create AI analysis record with ENHANCED AI results
        model_version = "enhanced_ai_v2.0" if ENHANCED_AI_AVAILABLE else ("full_ai_pipeline_v1.0" if FULL_AI_AVAILABLE else "lightweight_ai_v1.0")
        if ai_result.get('thermal_calibration_used', False):
            model_version += "_flir_calibrated"
        if ai_result.get('yolo_model_used'):
            model_version += f"_{ai_result.get('yolo_model_used', 'unknown')}"
        
        ai_analysis = AIAnalysis(
            thermal_scan_id=scan.id,
            model_version=model_version,
            analysis_status="completed",
            processing_duration_seconds=ai_result.get('processing_time', 0),
            
            # Quality assessment
            is_good_quality=ai_result['is_good_quality'],
            quality_score=ai_result['quality_score'],
            
            # Temperature analysis
            ambient_temperature=scan.ambient_temperature or 34.0,
            max_temperature_detected=ai_result['max_temperature'],
            min_temperature_detected=ai_result['min_temperature'],
            avg_temperature=ai_result['avg_temperature'],
            
            # Hotspot analysis
            total_hotspots=ai_result['total_hotspots'],
            critical_hotspots=ai_result['critical_hotspots'],
            potential_hotspots=ai_result['potential_hotspots'],
            normal_zones=10 - ai_result['total_hotspots'],  # Assuming 10 zones total
            
            # Component detection
            total_components_detected=ai_result.get('total_components', component_summary.get('nuts_bolts', 0) + component_summary.get('mid_span_joints', 0) + component_summary.get('polymer_insulators', 0)),
            nuts_bolts_count=component_summary.get('nuts_bolts', 0),
            mid_span_joints_count=component_summary.get('mid_span_joints', 0),
            polymer_insulators_count=component_summary.get('polymer_insulators', 0),
            
            # Risk assessment
            overall_risk_level=ai_result['overall_risk_level'],
            risk_score=ai_result['risk_score'],
            requires_immediate_attention=ai_result['requires_immediate_attention'],
            summary_text=ai_result['summary_text']
        )
        
        db.add(ai_analysis)
        db.commit()
        db.refresh(ai_analysis)
        
        # Create detection records for individual components/detections
        if FULL_AI_AVAILABLE and components:
            for component_data in components:
                detection = Detection(
                    ai_analysis_id=ai_analysis.id,
                    component_type=component_data.get('component_type', 'unknown'),
                    confidence=component_data.get('confidence', 0.0),
                    bbox_x=component_data.get('bbox', [0, 0, 0, 0])[0],
                    bbox_y=component_data.get('bbox', [0, 0, 0, 0])[1],
                    bbox_width=component_data.get('bbox', [0, 0, 0, 0])[2],
                    bbox_height=component_data.get('bbox', [0, 0, 0, 0])[3] if len(component_data.get('bbox', [0, 0, 0, 0])) > 3 else component_data.get('bbox', [0, 0, 0, 0])[2],
                    temperature_reading=component_data.get('region_max_temp', scan.ambient_temperature or 34.0),
                    hotspot_classification=component_data.get('defect_type', 'normal')
                )
                db.add(detection)
        else:
            # Create detection records from lightweight analysis
            for detection_data in ai_result.get('components', []):
                detection = Detection(
                    ai_analysis_id=ai_analysis.id,
                    component_type=detection_data.get('component_type', 'unknown'),
                    confidence=detection_data.get('confidence', 0.0),
                    bbox_x=detection_data.get('bbox', [0, 0, 0, 0])[0],
                    bbox_y=detection_data.get('bbox', [0, 0, 0, 0])[1],
                    bbox_width=detection_data.get('bbox', [0, 0, 0, 0])[2],
                    bbox_height=detection_data.get('bbox', [0, 0, 0, 0])[3] if len(detection_data.get('bbox', [0, 0, 0, 0])) > 3 else detection_data.get('bbox', [0, 0, 0, 0])[2],
                    temperature_reading=detection_data.get('temperature', scan.ambient_temperature or 34.0),
                    hotspot_classification=detection_data.get('hotspot_classification', 'normal')
                )
                db.add(detection)
        
        db.commit()
        
        logger.info(f"✅ FULL AI analysis saved for {scan.original_filename}")
        return ai_analysis
        
    except Exception as e:
        logger.error(f"❌ FULL AI analysis failed for {scan.original_filename}: {e}")
        
        # Create failed analysis record with proper defaults
        ai_analysis = AIAnalysis(
            thermal_scan_id=scan.id,
            model_version="full_ai_pipeline_v1.0" if FULL_AI_AVAILABLE else "lightweight_ai_v1.0",
            analysis_status="failed",
            error_message=str(e),
            summary_text=f"Analysis failed: {str(e)}",
            
            # Required fields with defaults
            is_good_quality=False,
            quality_score=0.0,
            ambient_temperature=scan.ambient_temperature or 34.0,
            max_temperature_detected=34.0,
            min_temperature_detected=34.0,
            avg_temperature=34.0,
            temperature_variance=0.0,
            total_hotspots=0,
            critical_hotspots=0,
            potential_hotspots=0,
            normal_zones=0,
            total_components_detected=0,
            nuts_bolts_count=0,
            mid_span_joints_count=0,
            polymer_insulators_count=0,
            overall_risk_level="unknown",
            risk_score=0.0,
            requires_immediate_attention=False
        )
        
        db.add(ai_analysis)
        db.commit()
        db.refresh(ai_analysis)
        
        return ai_analysis 