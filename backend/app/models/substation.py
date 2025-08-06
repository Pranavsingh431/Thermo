from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.database import Base

class Substation(Base):
    __tablename__ = "substations"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Basic information
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, index=True, nullable=False)  # e.g., "SALSETTE_CAMP"
    voltage_level = Column(String(50))  # e.g., "400kV", "220kV"
    
    # Location data
    latitude = Column(Float, nullable=False, index=True)
    longitude = Column(Float, nullable=False, index=True)
    address = Column(Text)
    city = Column(String(100), default="Mumbai")
    state = Column(String(100), default="Maharashtra")
    country = Column(String(100), default="India")
    
    # Geographical boundaries (for geo-fencing)
    boundary_coordinates = Column(JSON)  # Array of lat/lng points defining boundary polygon
    inspection_radius = Column(Float, default=500.0)  # Meters for automatic asset matching
    
    # Operational information
    commissioning_date = Column(DateTime)
    capacity_mw = Column(Float)
    num_circuits = Column(Integer)
    num_transformers = Column(Integer)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    maintenance_status = Column(String(50), default="operational")  # operational, maintenance, shutdown
    
    # Contact information
    control_room_phone = Column(String(20))
    engineer_in_charge = Column(String(255))
    emergency_contact = Column(String(20))
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Notes
    description = Column(Text)
    special_instructions = Column(Text)
    
    # Relationships
    thermal_scans = relationship("ThermalScan", back_populates="substation")
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_substation_location', 'latitude', 'longitude'),
        Index('idx_substation_active', 'is_active'),
        Index('idx_substation_voltage', 'voltage_level'),
    )
    
    def is_point_within_boundary(self, latitude: float, longitude: float) -> bool:
        """Check if a GPS point is within substation boundary"""
        if not self.boundary_coordinates:
            # Use circular boundary based on inspection_radius
            from geopy.distance import geodesic
            distance = geodesic(
                (self.latitude, self.longitude),
                (latitude, longitude)
            ).meters
            return distance <= self.inspection_radius
        
        # TODO: Implement polygon boundary check using shapely
        # For now, use simple radius check
        from geopy.distance import geodesic
        distance = geodesic(
            (self.latitude, self.longitude),
            (latitude, longitude)
        ).meters
        return distance <= self.inspection_radius
    
    def get_distance_to_point(self, latitude: float, longitude: float) -> float:
        """Get distance in meters to a GPS point"""
        from geopy.distance import geodesic
        return geodesic(
            (self.latitude, self.longitude),
            (latitude, longitude)
        ).meters
    
    @property
    def coordinates(self) -> dict:
        """Get coordinates as dict"""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude
        }
    
    def __repr__(self):
        return f"<Substation(id={self.id}, name='{self.name}', code='{self.code}')>" 