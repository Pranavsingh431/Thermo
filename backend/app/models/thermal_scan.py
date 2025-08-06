from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base

class ThermalScan(Base):
    __tablename__ = "thermal_scans"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # File information
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500))  # Path where file is stored (temporarily)
    file_size_bytes = Column(Integer)
    file_hash = Column(String(64), index=True)  # SHA-256 hash for deduplication
    
    # FLIR image metadata
    camera_model = Column(String(100))  # e.g., "FLIR T560"
    camera_software_version = Column(String(50))
    image_width = Column(Integer)
    image_height = Column(Integer)
    
    # GPS and location data (extracted from EXIF)
    latitude = Column(Float, index=True)
    longitude = Column(Float, index=True)
    altitude = Column(Float)
    gps_timestamp = Column(DateTime)
    gps_accuracy = Column(Float)  # GPS accuracy in meters
    
    # Image capture information
    capture_timestamp = Column(DateTime, nullable=False, index=True)
    ambient_temperature = Column(Float)  # If available from EXIF
    camera_settings = Column(JSON)  # Store camera settings as JSON
    
    # Processing status
    processing_status = Column(String(50), default="pending", nullable=False, index=True)
    # Status: pending, processing, completed, failed, skipped
    processing_started_at = Column(DateTime)
    processing_completed_at = Column(DateTime)
    processing_duration_seconds = Column(Float)
    
    # Quality assessment (from AI)
    is_good_quality = Column(Boolean)
    quality_score = Column(Float)  # 0.0 to 1.0
    quality_issues = Column(JSON)  # Array of quality issues detected
    
    # Batch information
    batch_id = Column(String(100), index=True)  # UUID for batch processing
    batch_sequence = Column(Integer)  # Order in batch
    
    # Relationships
    substation_id = Column(Integer, ForeignKey("substations.id"), index=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    substation = relationship("Substation", back_populates="thermal_scans")
    uploaded_by_user = relationship("User", back_populates="thermal_scans")
    ai_analysis = relationship("AIAnalysis", back_populates="thermal_scan", uselist=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Notes and tags
    notes = Column(Text)
    tags = Column(JSON)  # Array of tags for categorization
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_thermal_scan_location', 'latitude', 'longitude'),
        Index('idx_thermal_scan_status_created', 'processing_status', 'created_at'),
        Index('idx_thermal_scan_batch', 'batch_id', 'batch_sequence'),
        Index('idx_thermal_scan_substation_date', 'substation_id', 'capture_timestamp'),
        Index('idx_thermal_scan_quality', 'is_good_quality', 'quality_score'),
    )
    
    @property
    def coordinates(self) -> dict:
        """Get GPS coordinates as dict"""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "altitude": self.altitude
        }
    
    @property
    def processing_time_str(self) -> str:
        """Get processing duration as human readable string"""
        if not self.processing_duration_seconds:
            return "Not processed"
        
        duration = self.processing_duration_seconds
        if duration < 60:
            return f"{duration:.1f} seconds"
        elif duration < 3600:
            return f"{duration/60:.1f} minutes"
        else:
            return f"{duration/3600:.1f} hours"
    
    @property
    def file_size_str(self) -> str:
        """Get file size as human readable string"""
        if not self.file_size_bytes:
            return "Unknown"
        
        size = self.file_size_bytes
        if size < 1024:
            return f"{size} B"
        elif size < 1024**2:
            return f"{size/1024:.1f} KB"
        elif size < 1024**3:
            return f"{size/(1024**2):.1f} MB"
        else:
            return f"{size/(1024**3):.1f} GB"
    
    def update_processing_status(self, status: str) -> None:
        """Update processing status with timestamps"""
        self.processing_status = status
        
        if status == "processing":
            self.processing_started_at = func.now()
        elif status in ["completed", "failed", "skipped"]:
            self.processing_completed_at = func.now()
            if self.processing_started_at:
                # Calculate duration
                from datetime import datetime
                now = datetime.utcnow()
                start = self.processing_started_at
                if isinstance(start, datetime):
                    self.processing_duration_seconds = (now - start).total_seconds()
    
    def __repr__(self):
        return f"<ThermalScan(id={self.id}, filename='{self.original_filename}', status='{self.processing_status}')>" 