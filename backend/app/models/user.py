from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from passlib.context import CryptContext

from app.database import Base

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(Base):
    __tablename__ = "users"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Authentication fields
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # User information
    full_name = Column(String(255), nullable=False)
    employee_id = Column(String(50), unique=True, index=True)
    department = Column(String(100))
    designation = Column(String(100))
    
    # Role and permissions
    role = Column(String(50), default="operator", nullable=False)  # admin, engineer, operator, viewer
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    
    # Contact information
    phone_number = Column(String(20))
    notification_email = Column(String(255))  # For alerts, can be different from login email
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    login_count = Column(Integer, default=0)
    
    # Notes for admin
    notes = Column(Text)
    
    # Relationships
    thermal_scans = relationship("ThermalScan", back_populates="uploaded_by_user")
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_user_role_active', 'role', 'is_active'),
        Index('idx_user_department', 'department'),
        Index('idx_user_created', 'created_at'),
    )
    
    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(password, self.hashed_password)
    
    def set_password(self, password: str) -> None:
        """Set hashed password"""
        self.hashed_password = pwd_context.hash(password)
    
    @property
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self.role == "admin"
    
    @property
    def is_engineer(self) -> bool:
        """Check if user is engineer"""
        return self.role in ["admin", "engineer"]
    
    @property
    def can_upload(self) -> bool:
        """Check if user can upload thermal images"""
        return self.role in ["admin", "engineer", "operator"]
    
    @property
    def can_view_all_data(self) -> bool:
        """Check if user can view all data"""
        return self.role in ["admin", "engineer"]
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', role='{self.role}')>" 