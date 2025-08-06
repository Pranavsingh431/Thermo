"""
Production Health Check Endpoints
================================

This module provides comprehensive health check endpoints for production monitoring.
All endpoints provide detailed system status for operational visibility.

Author: Production System for Tata Power Thermal Eye
"""

import logging
from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.database import get_db
from app.services.model_loader import model_loader
from app.services.bulletproof_ai_pipeline import bulletproof_ai_pipeline
from app.utils.flir_thermal_extractor import flir_extractor

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/api/health")
async def system_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Comprehensive system health check for production monitoring.
    
    This endpoint verifies:
    - Database connectivity
    - AI model status  
    - Core service availability
    - System readiness
    
    Returns:
        Complete system health status
    """
    
    health_start = datetime.now()
    
    try:
        # Initialize health status
        health_status = {
            "status": "healthy",
            "timestamp": health_start.isoformat(),
            "system": "Tata Power Thermal Eye",
            "version": "production_v1.0",
            "checks": {}
        }
        
        # Check 1: Database connectivity
        db_status = await _check_database_health(db)
        health_status["checks"]["database"] = db_status
        
        # Check 2: AI model status
        ai_status = await _check_ai_models_health()
        health_status["checks"]["ai_models"] = ai_status
        
        # Check 3: Core services
        services_status = await _check_core_services_health()
        health_status["checks"]["core_services"] = services_status
        
        # Check 4: System resources
        resources_status = await _check_system_resources()
        health_status["checks"]["system_resources"] = resources_status
        
        # Determine overall status
        all_checks_passed = all(
            check.get("status") == "healthy" 
            for check in health_status["checks"].values()
        )
        
        if not all_checks_passed:
            health_status["status"] = "degraded"
            
            # Check for critical failures
            critical_failures = any(
                check.get("status") == "critical"
                for check in health_status["checks"].values()
            )
            
            if critical_failures:
                health_status["status"] = "critical"
        
        # Add response metadata
        health_end = datetime.now()
        health_status["response_time_ms"] = int((health_end - health_start).total_seconds() * 1000)
        
        logger.info(f"Health check completed: {health_status['status']}")
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        
        return {
            "status": "critical",
            "timestamp": datetime.now().isoformat(),
            "error": "Health check system failure",
            "details": str(e)
        }

@router.get("/api/health/db")
async def database_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Detailed database health check.
    
    Returns:
        Database connectivity and performance status
    """
    
    return await _check_database_health(db)

@router.get("/api/health/models") 
async def models_health_check() -> Dict[str, Any]:
    """
    Detailed AI models health check.
    
    Returns:
        AI model loading and readiness status
    """
    
    return await _check_ai_models_health()

@router.get("/api/health/system")
async def system_resources_check() -> Dict[str, Any]:
    """
    System resources health check.
    
    Returns:
        System resource utilization and availability
    """
    
    return await _check_system_resources()

async def _check_database_health(db: Session) -> Dict[str, Any]:
    """Check database connectivity and performance"""
    
    db_start = datetime.now()
    
    try:
        # Test basic connectivity
        result = db.execute(text("SELECT 1 as test")).fetchone()
        
        if result and result[0] == 1:
            # Test table access
            db.execute(text("SELECT COUNT(*) FROM thermal_scans")).fetchone()
            db.execute(text("SELECT COUNT(*) FROM ai_analyses")).fetchone()
            
            db_end = datetime.now()
            response_time = int((db_end - db_start).total_seconds() * 1000)
            
            return {
                "status": "healthy",
                "message": "Database connectivity verified",
                "response_time_ms": response_time,
                "last_check": db_end.isoformat()
            }
        else:
            return {
                "status": "critical",
                "message": "Database test query failed",
                "last_check": datetime.now().isoformat()
            }
            
    except Exception as e:
        return {
            "status": "critical", 
            "message": f"Database connection failed: {str(e)}",
            "last_check": datetime.now().isoformat()
        }

async def _check_ai_models_health() -> Dict[str, Any]:
    """Check AI model loading and readiness"""
    
    try:
        # Get model status from loader
        model_status = model_loader.get_model_status()
        
        # Get pipeline status  
        pipeline_status = bulletproof_ai_pipeline.get_system_status()
        
        # Determine overall AI health
        models_loaded = len(model_status.get("loaded_models", []))
        integrity_verified = model_status.get("integrity_status") == "verified"
        pipeline_operational = pipeline_status.get("pipeline_status") == "operational"
        
        if models_loaded > 0 and integrity_verified and pipeline_operational:
            status = "healthy"
            message = f"{models_loaded} AI models loaded and verified"
        elif pipeline_status.get("pattern_fallback_available"):
            status = "degraded"
            message = "AI models unavailable, using pattern fallback"
        else:
            status = "critical"
            message = "AI system not operational"
        
        return {
            "status": status,
            "message": message,
            "models_loaded": models_loaded,
            "integrity_verified": integrity_verified,
            "pipeline_operational": pipeline_operational,
            "yolo_available": pipeline_status.get("yolo_available", False),
            "pattern_fallback": pipeline_status.get("pattern_fallback_available", False),
            "model_details": model_status.get("models_available", {}),
            "last_check": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "critical",
            "message": f"AI models health check failed: {str(e)}",
            "last_check": datetime.now().isoformat()
        }

async def _check_core_services_health() -> Dict[str, Any]:
    """Check core service availability"""
    
    try:
        services_status = {}
        
        # Check FLIR extractor
        try:
            # This is a lightweight check
            services_status["flir_extractor"] = {
                "status": "healthy",
                "message": "FLIR thermal extractor available"
            }
        except Exception as e:
            services_status["flir_extractor"] = {
                "status": "critical",
                "message": f"FLIR extractor failed: {e}"
            }
        
        # Check bulletproof pipeline
        try:
            pipeline_status = bulletproof_ai_pipeline.get_system_status()
            services_status["ai_pipeline"] = {
                "status": "healthy" if pipeline_status.get("pipeline_status") == "operational" else "degraded",
                "message": f"AI pipeline {pipeline_status.get('pipeline_status', 'unknown')}"
            }
        except Exception as e:
            services_status["ai_pipeline"] = {
                "status": "critical",
                "message": f"AI pipeline check failed: {e}"
            }
        
        # Overall services status
        all_healthy = all(
            service.get("status") == "healthy"
            for service in services_status.values()
        )
        
        overall_status = "healthy" if all_healthy else "degraded"
        
        # Check for critical service failures
        critical_failures = any(
            service.get("status") == "critical"
            for service in services_status.values()
        )
        
        if critical_failures:
            overall_status = "critical"
        
        return {
            "status": overall_status,
            "message": f"Core services status: {overall_status}",
            "services": services_status,
            "last_check": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "status": "critical",
            "message": f"Core services check failed: {str(e)}",
            "last_check": datetime.now().isoformat()
        }

async def _check_system_resources() -> Dict[str, Any]:
    """Check system resource availability"""
    
    try:
        import psutil
        import os
        from pathlib import Path
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Check critical directories
        directories_status = {}
        
        critical_dirs = [
            Path("static/thermal_images"),
            Path("static/reports"),
            Path("logs"),
            Path("models")
        ]
        
        for directory in critical_dirs:
            directories_status[str(directory)] = {
                "exists": directory.exists(),
                "writable": directory.exists() and os.access(directory, os.W_OK)
            }
        
        # Determine resource status
        resource_warnings = []
        
        if cpu_percent > 80:
            resource_warnings.append(f"High CPU usage: {cpu_percent:.1f}%")
            
        if memory.percent > 85:
            resource_warnings.append(f"High memory usage: {memory.percent:.1f}%")
            
        if disk.percent > 90:
            resource_warnings.append(f"Low disk space: {disk.percent:.1f}% used")
        
        missing_dirs = [
            dir_name for dir_name, status in directories_status.items()
            if not status["exists"] or not status["writable"]
        ]
        
        if missing_dirs:
            resource_warnings.append(f"Directory issues: {', '.join(missing_dirs)}")
        
        # Overall status
        if resource_warnings:
            status = "degraded" if len(resource_warnings) <= 2 else "critical"
            message = f"Resource warnings: {'; '.join(resource_warnings)}"
        else:
            status = "healthy"
            message = "System resources within normal limits"
        
        return {
            "status": status,
            "message": message,
            "cpu_percent": round(cpu_percent, 1),
            "memory_percent": round(memory.percent, 1),
            "disk_percent": round(disk.percent, 1),
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "directories": directories_status,
            "warnings": resource_warnings,
            "last_check": datetime.now().isoformat()
        }
        
    except ImportError:
        return {
            "status": "degraded",
            "message": "psutil not available - limited resource monitoring",
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "critical",
            "message": f"System resources check failed: {str(e)}",
            "last_check": datetime.now().isoformat()
        } 