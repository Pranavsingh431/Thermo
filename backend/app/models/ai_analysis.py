from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base

class AIAnalysis(Base):
    __tablename__ = "ai_analyses"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to thermal scan
    thermal_scan_id = Column(Integer, ForeignKey("thermal_scans.id"), nullable=False, unique=True, index=True)
    
    # AI model information
    model_version = Column(String(100), nullable=False)  # e.g., "yolo_nas_s_mobilenet_v3"
    yolo_model_path = Column(String(255))
    quality_model_path = Column(String(255))
    
    # Overall analysis results
    analysis_status = Column(String(50), default="pending", nullable=False)  # pending, completed, failed
    analysis_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    processing_duration_seconds = Column(Float)
    
    # Quality assessment results
    is_good_quality = Column(Boolean, nullable=False)
    quality_score = Column(Float, nullable=False)  # 0.0 to 1.0
    quality_issues = Column(JSON)  # Array of issues: ["blurry", "overexposed", "underexposed"]
    
    # Thermal analysis results
    ambient_temperature = Column(Float)  # Detected or provided ambient temperature
    max_temperature_detected = Column(Float)  # Highest temperature found
    min_temperature_detected = Column(Float)  # Lowest temperature found
    avg_temperature = Column(Float)  # Average temperature
    temperature_variance = Column(Float)  # Temperature variance across image
    
    # Hotspot analysis
    total_hotspots = Column(Integer, default=0)
    critical_hotspots = Column(Integer, default=0)  # Above critical threshold
    potential_hotspots = Column(Integer, default=0)  # Above potential threshold
    normal_zones = Column(Integer, default=0)
    
    # Component detection summary
    total_components_detected = Column(Integer, default=0)
    nuts_bolts_count = Column(Integer, default=0)
    mid_span_joints_count = Column(Integer, default=0)
    polymer_insulators_count = Column(Integer, default=0)
    
    # Risk assessment
    overall_risk_level = Column(String(50))  # low, medium, high, critical
    risk_score = Column(Float)  # 0.0 to 100.0
    requires_immediate_attention = Column(Boolean, default=False)
    
    # Analysis summary
    summary_text = Column(Text)  # Human-readable summary
    recommendations = Column(JSON)  # Array of recommended actions
    
    # Error handling
    error_message = Column(Text)  # If analysis failed
    warnings = Column(JSON)  # Array of warnings during processing
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    thermal_scan = relationship("ThermalScan", back_populates="ai_analysis")
    detections = relationship("Detection", back_populates="ai_analysis", cascade="all, delete-orphan")
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_ai_analysis_status', 'analysis_status'),
        Index('idx_ai_analysis_risk', 'overall_risk_level', 'risk_score'),
        Index('idx_ai_analysis_hotspots', 'critical_hotspots', 'potential_hotspots'),
        Index('idx_ai_analysis_quality', 'is_good_quality', 'quality_score'),
        Index('idx_ai_analysis_attention', 'requires_immediate_attention'),
    )
    
    @property
    def total_issues(self) -> int:
        """Get total number of issues detected"""
        return self.critical_hotspots + self.potential_hotspots
    
    @property
    def detection_summary(self) -> dict:
        """Get summary of detections"""
        return {
            "total_components": self.total_components_detected,
            "nuts_bolts": self.nuts_bolts_count,
            "mid_span_joints": self.mid_span_joints_count,
            "polymer_insulators": self.polymer_insulators_count
        }
    
    @property
    def hotspot_summary(self) -> dict:
        """Get summary of hotspots"""
        return {
            "total": self.total_hotspots,
            "critical": self.critical_hotspots,
            "potential": self.potential_hotspots,
            "normal": self.normal_zones
        }
    
    def __repr__(self):
        return f"<AIAnalysis(id={self.id}, thermal_scan_id={self.thermal_scan_id}, risk='{self.overall_risk_level}')>"


class Detection(Base):
    __tablename__ = "detections"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Foreign key to AI analysis
    ai_analysis_id = Column(Integer, ForeignKey("ai_analyses.id"), nullable=False, index=True)
    
    # Detection information
    component_type = Column(String(100), nullable=False, index=True)  # nuts_bolts, mid_span_joint, polymer_insulator
    confidence = Column(Float, nullable=False)  # 0.0 to 1.0
    
    # Bounding box coordinates (relative to image dimensions)
    bbox_x = Column(Float, nullable=False)  # X coordinate (0.0 to 1.0)
    bbox_y = Column(Float, nullable=False)  # Y coordinate (0.0 to 1.0)
    bbox_width = Column(Float, nullable=False)  # Width (0.0 to 1.0)
    bbox_height = Column(Float, nullable=False)  # Height (0.0 to 1.0)
    
    # Center point coordinates
    center_x = Column(Float, nullable=False)
    center_y = Column(Float, nullable=False)
    
    # Thermal analysis for this detection
    max_temperature = Column(Float)  # Maximum temperature in this region
    avg_temperature = Column(Float)  # Average temperature in this region
    min_temperature = Column(Float)  # Minimum temperature in this region
    
    # Hotspot classification
    hotspot_classification = Column(String(50), nullable=False)  # normal, potential, critical
    temperature_above_ambient = Column(Float)  # Temperature difference from ambient
    
    # Risk assessment for this component
    risk_level = Column(String(50))  # low, medium, high, critical
    risk_factors = Column(JSON)  # Array of risk factors identified
    
    # Additional metadata
    area_pixels = Column(Integer)  # Area of detection in pixels
    aspect_ratio = Column(Float)  # Width/height ratio
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    ai_analysis = relationship("AIAnalysis", back_populates="detections")
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_detection_component', 'component_type'),
        Index('idx_detection_hotspot', 'hotspot_classification'),
        Index('idx_detection_risk', 'risk_level'),
        Index('idx_detection_confidence', 'confidence'),
        Index('idx_detection_temperature', 'max_temperature'),
    )
    
    @property
    def bbox_dict(self) -> dict:
        """Get bounding box as dictionary"""
        return {
            "x": self.bbox_x,
            "y": self.bbox_y,
            "width": self.bbox_width,
            "height": self.bbox_height
        }
    
    @property
    def center_point(self) -> dict:
        """Get center point as dictionary"""
        return {
            "x": self.center_x,
            "y": self.center_y
        }
    
    @property
    def is_hotspot(self) -> bool:
        """Check if this detection is a hotspot"""
        return self.hotspot_classification in ["potential", "critical"]
    
    @property
    def is_critical(self) -> bool:
        """Check if this detection is critical"""
        return self.hotspot_classification == "critical" or self.risk_level == "critical"
    
    def __repr__(self):
        return f"<Detection(id={self.id}, component='{self.component_type}', hotspot='{self.hotspot_classification}')>" 