"""
Thermal image upload API routes
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging
from datetime import datetime

from app.database import get_db
from app.models.user import User
from app.models.substation import Substation
from app.models.thermal_scan import ThermalScan
from app.utils.auth import get_current_user, require_permission
from app.utils.thermal_processing import thermal_processor
from app.services.thermal_analysis import process_thermal_batch

logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic models
class UploadResponse(BaseModel):
    batch_id: str
    total_files: int
    successful_uploads: int
    failed_uploads: int
    processing_status: str
    message: str

class FileUploadStatus(BaseModel):
    filename: str
    status: str
    message: str
    thermal_scan_id: Optional[int] = None

class BatchStatus(BaseModel):
    batch_id: str
    total_images: int
    processed_images: int
    failed_images: int
    status: str
    created_at: str
    processing_duration: Optional[str] = None

@router.post("/thermal-images", response_model=UploadResponse)
async def upload_thermal_images(
    files: List[UploadFile] = File(...),
    ambient_temperature: Optional[float] = Form(34.0),
    notes: Optional[str] = Form(None),
    current_user: User = Depends(require_permission("upload")),
    db: Session = Depends(get_db)
):
    """Upload multiple thermal images for processing"""
    
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided"
        )
    
    # Validate file count
    if len(files) > 5000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 5000 files allowed per batch"
        )
    
    # Create batch ID
    batch_id = thermal_processor.create_batch_id()
    successful_uploads = 0
    failed_uploads = 0
    upload_results = []
    
    # Get all substations for location matching
    substations = db.query(Substation).filter(Substation.is_active == True).all()
    
    logger.info(f"Starting batch upload {batch_id} with {len(files)} files by user {current_user.username}")
    
    for sequence, file in enumerate(files, 1):
        try:
            # Read file content
            file_content = await file.read()
            file_size = len(file_content)
            
            # Validate file
            is_valid, validation_message = thermal_processor.validate_image_file(file.filename, file_size)
            if not is_valid:
                failed_uploads += 1
                upload_results.append(FileUploadStatus(
                    filename=file.filename,
                    status="failed",
                    message=validation_message
                ))
                continue
            
            # Calculate file hash for deduplication
            file_hash = thermal_processor.calculate_file_hash(file_content)
            
            # Check for duplicate
            existing_scan = db.query(ThermalScan).filter(ThermalScan.file_hash == file_hash).first()
            if existing_scan:
                logger.warning(f"Duplicate file detected: {file.filename} (hash: {file_hash})")
                upload_results.append(FileUploadStatus(
                    filename=file.filename,
                    status="skipped",
                    message="Duplicate file already processed",
                    thermal_scan_id=existing_scan.id
                ))
                continue
            
            # Save file temporarily
            file_path = thermal_processor.save_uploaded_file(file_content, file.filename, batch_id)
            
            # Extract metadata
            metadata = thermal_processor.extract_image_metadata(file_path)
            
            # Find matching substation
            substation_id = None
            if metadata.get('latitude') and metadata.get('longitude'):
                substation_id = thermal_processor.find_matching_substation(
                    metadata['latitude'], 
                    metadata['longitude'], 
                    substations
                )
            
            # Create thermal scan record
            thermal_scan = ThermalScan(
                original_filename=file.filename,
                file_path=file_path,
                file_size_bytes=file_size,
                file_hash=file_hash,
                camera_model=metadata.get('camera_model'),
                camera_software_version=metadata.get('camera_software_version'),
                image_width=metadata.get('image_width'),
                image_height=metadata.get('image_height'),
                latitude=metadata.get('latitude'),
                longitude=metadata.get('longitude'),
                altitude=metadata.get('altitude'),
                gps_timestamp=metadata.get('gps_timestamp'),
                capture_timestamp=metadata.get('capture_timestamp') or datetime.now(),
                ambient_temperature=ambient_temperature,
                camera_settings=metadata.get('camera_settings'),
                batch_id=batch_id,
                batch_sequence=sequence,
                substation_id=substation_id,
                uploaded_by=current_user.id,
                notes=notes
            )
            
            db.add(thermal_scan)
            db.commit()
            db.refresh(thermal_scan)
            
            successful_uploads += 1
            upload_results.append(FileUploadStatus(
                filename=file.filename,
                status="uploaded",
                message="Successfully uploaded and queued for processing",
                thermal_scan_id=thermal_scan.id
            ))
            
        except Exception as e:
            logger.error(f"Failed to process file {file.filename}: {e}")
            failed_uploads += 1
            upload_results.append(FileUploadStatus(
                filename=file.filename,
                status="failed",
                message=f"Processing error: {str(e)}"
            ))
    
    # Start background processing if any files were uploaded successfully
    processing_status = "idle"
    if successful_uploads > 0:
        # Trigger background processing
        asyncio.create_task(process_thermal_batch(batch_id, db, current_user.id))
        processing_status = "queued"
        
        message = f"Batch {batch_id}: {successful_uploads} files uploaded successfully, {failed_uploads} failed. Processing started."
    else:
        message = f"Batch {batch_id}: No files processed successfully. {failed_uploads} failed."
    
    logger.info(f"Batch upload {batch_id} completed: {successful_uploads} success, {failed_uploads} failed")
    
    return UploadResponse(
        batch_id=batch_id,
        total_files=len(files),
        successful_uploads=successful_uploads,
        failed_uploads=failed_uploads,
        processing_status=processing_status,
        message=message
    )

@router.get("/batch/{batch_id}/status", response_model=BatchStatus)
async def get_batch_status(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get processing status of a batch"""
    
    # Get all thermal scans in this batch
    scans = db.query(ThermalScan).filter(ThermalScan.batch_id == batch_id).all()
    
    if not scans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    # Check if user has access to this batch
    if not current_user.can_view_all_data:
        # Users can only see their own batches
        if not any(scan.uploaded_by == current_user.id for scan in scans):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this batch"
            )
    
    # Calculate status
    total_images = len(scans)
    processed_images = len([s for s in scans if s.processing_status == "completed"])
    failed_images = len([s for s in scans if s.processing_status == "failed"])
    pending_images = len([s for s in scans if s.processing_status == "pending"])
    processing_images = len([s for s in scans if s.processing_status == "processing"])
    
    # Determine overall status
    if failed_images == total_images:
        overall_status = "failed"
    elif processed_images == total_images:
        overall_status = "completed"
    elif processing_images > 0:
        overall_status = "processing"
    elif pending_images > 0:
        overall_status = "pending"
    else:
        overall_status = "unknown"
    
    # Calculate processing duration
    processing_duration = None
    if scans:
        first_scan = min(scans, key=lambda x: x.created_at)
        completed_scans = [s for s in scans if s.processing_completed_at]
        if completed_scans:
            last_completed = max(completed_scans, key=lambda x: x.processing_completed_at)
            duration = (last_completed.processing_completed_at - first_scan.created_at).total_seconds()
            processing_duration = f"{duration:.1f} seconds"
    
    return BatchStatus(
        batch_id=batch_id,
        total_images=total_images,
        processed_images=processed_images,
        failed_images=failed_images,
        status=overall_status,
        created_at=scans[0].created_at.isoformat() if scans else "",
        processing_duration=processing_duration
    )

@router.get("/batch/{batch_id}/files", response_model=List[FileUploadStatus])
async def get_batch_files(
    batch_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed status of all files in a batch"""
    
    scans = db.query(ThermalScan).filter(ThermalScan.batch_id == batch_id).all()
    
    if not scans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    # Check access permissions
    if not current_user.can_view_all_data:
        if not any(scan.uploaded_by == current_user.id for scan in scans):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this batch"
            )
    
    return [
        FileUploadStatus(
            filename=scan.original_filename,
            status=scan.processing_status,
            message=f"Processing time: {scan.processing_time_str}",
            thermal_scan_id=scan.id
        )
        for scan in sorted(scans, key=lambda x: x.batch_sequence)
    ]

@router.delete("/batch/{batch_id}")
async def delete_batch(
    batch_id: str,
    current_user: User = Depends(require_permission("admin")),
    db: Session = Depends(get_db)
):
    """Delete a batch and all associated data (admin only)"""
    
    scans = db.query(ThermalScan).filter(ThermalScan.batch_id == batch_id).all()
    
    if not scans:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Batch not found"
        )
    
    # Delete all thermal scans (cascade will handle AI analyses)
    for scan in scans:
        db.delete(scan)
    
    # Clean up files
    thermal_processor.cleanup_batch_files(batch_id)
    
    db.commit()
    
    logger.info(f"Batch {batch_id} deleted by admin {current_user.username}")
    
    return {"message": f"Batch {batch_id} deleted successfully"}

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "upload"}    