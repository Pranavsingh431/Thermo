#!/usr/bin/env python3
"""
Create test users and sample data for Thermal Inspection System
"""

import sys
import os
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal, init_db
from app.models.user import User
from app.models.substation import Substation

def create_test_data():
    """Create test users and substations"""
    print("🔧 Creating test data...")
    
    db = SessionLocal()
    
    try:
        # Create admin user
        admin_user = User(
            username="admin",
            email="admin@tatapower.com",
            full_name="System Administrator",
            employee_id="TP_ADMIN",
            department="IT",
            designation="System Admin",
            role="admin"
        )
        admin_user.set_password("admin123")
        db.add(admin_user)
        
        # Create engineer user
        engineer_user = User(
            username="engineer",
            email="engineer@tatapower.com",
            full_name="Senior Electrical Engineer",
            employee_id="TP_ENG001",
            department="Electrical",
            designation="Senior Engineer",
            role="engineer"
        )
        engineer_user.set_password("engineer123")
        db.add(engineer_user)
        
        # Create operator user
        operator_user = User(
            username="operator",
            email="operator@tatapower.com",
            full_name="Field Operator",
            employee_id="TP_OPR001",
            department="Operations",
            designation="Field Operator",
            role="operator"
        )
        operator_user.set_password("operator123")
        db.add(operator_user)
        
        # Create Salsette Camp substation
        salsette_substation = Substation(
            name="Salsette Camp Substation",
            code="SALSETTE_CAMP",
            voltage_level="400kV",
            latitude=19.1262,
            longitude=72.8897,
            address="Salsette Camp, Mumbai, Maharashtra",
            num_circuits=6,
            num_transformers=3,
            engineer_in_charge="Senior Electrical Engineer",
            control_room_phone="+91-22-1234567"
        )
        db.add(salsette_substation)
        
        # Create additional Mumbai substations
        mumbai_substations = [
            {
                "name": "Versova Substation",
                "code": "VERSOVA",
                "voltage_level": "220kV",
                "latitude": 19.1364,
                "longitude": 72.8081,
                "address": "Versova, Mumbai, Maharashtra"
            },
            {
                "name": "Bandra Substation", 
                "code": "BANDRA",
                "voltage_level": "400kV",
                "latitude": 19.0596,
                "longitude": 72.8295,
                "address": "Bandra, Mumbai, Maharashtra"
            },
            {
                "name": "Powai Substation",
                "code": "POWAI", 
                "voltage_level": "220kV",
                "latitude": 19.1197,
                "longitude": 72.9058,
                "address": "Powai, Mumbai, Maharashtra"
            }
        ]
        
        for sub_data in mumbai_substations:
            substation = Substation(
                name=sub_data["name"],
                code=sub_data["code"],
                voltage_level=sub_data["voltage_level"],
                latitude=sub_data["latitude"],
                longitude=sub_data["longitude"],
                address=sub_data["address"],
                num_circuits=4,
                num_transformers=2,
                engineer_in_charge="Electrical Engineer",
                control_room_phone="+91-22-1234567"
            )
            db.add(substation)
        
        db.commit()
        
        print("✅ Test data created successfully!")
        print("\n📋 Test Users Created:")
        print("👤 Admin: username='admin', password='admin123'")
        print("👤 Engineer: username='engineer', password='engineer123'") 
        print("👤 Operator: username='operator', password='operator123'")
        print("\n🏭 Substations Created:")
        print("🔌 Salsette Camp Substation")
        print("🔌 Versova Substation")
        print("🔌 Bandra Substation")
        print("🔌 Powai Substation")
        
    except Exception as e:
        print(f"❌ Error creating test data: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Initializing Thermal Inspection System Database...")
    init_db()
    create_test_data()
    print("\n🎉 Ready for testing!") 