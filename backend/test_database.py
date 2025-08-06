#!/usr/bin/env python3
"""
Test script to verify database models and setup
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, get_db, check_db_connection
from app.models import User, Substation, ThermalScan, AIAnalysis, Detection
from sqlalchemy.orm import Session
from datetime import datetime

def test_database_connection():
    """Test database connection"""
    print("🔧 Testing database connection...")
    if check_db_connection():
        print("✅ Database connection successful")
        return True
    else:
        print("❌ Database connection failed")
        return False

def create_tables():
    """Create all database tables"""
    print("🏗️ Creating database tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create tables: {e}")
        return False

def test_user_model():
    """Test User model operations"""
    print("👤 Testing User model...")
    
    try:
        db = next(get_db())
        
        # Create a test user
        test_user = User(
            email="test.engineer@tatapower.com",
            username="test_engineer",
            full_name="Test Engineer",
            employee_id="TP001",
            department="Electrical",
            designation="Senior Engineer",
            role="engineer"
        )
        test_user.set_password("testpassword123")
        
        db.add(test_user)
        db.commit()
        
        # Verify user was created
        created_user = db.query(User).filter(User.email == "test.engineer@tatapower.com").first()
        if created_user:
            print(f"✅ User created: {created_user.full_name} ({created_user.role})")
            print(f"✅ Password verification: {created_user.verify_password('testpassword123')}")
            print(f"✅ User permissions - can_upload: {created_user.can_upload}, is_engineer: {created_user.is_engineer}")
            return True
        else:
            print("❌ User creation failed")
            return False
            
    except Exception as e:
        print(f"❌ User model test failed: {e}")
        return False

def test_substation_model():
    """Test Substation model operations"""
    print("🏭 Testing Substation model...")
    
    try:
        db = next(get_db())
        
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
            engineer_in_charge="Test Engineer",
            control_room_phone="+91-22-1234567"
        )
        
        db.add(salsette_substation)
        db.commit()
        
        # Test GPS proximity check
        test_lat, test_lon = 19.1265, 72.8895  # Very close coordinates
        is_within = salsette_substation.is_point_within_boundary(test_lat, test_lon)
        distance = salsette_substation.get_distance_to_point(test_lat, test_lon)
        
        print(f"✅ Substation created: {salsette_substation.name}")
        print(f"✅ GPS test - Distance: {distance:.1f}m, Within boundary: {is_within}")
        return True
        
    except Exception as e:
        print(f"❌ Substation model test failed: {e}")
        return False

def test_thermal_scan_model():
    """Test ThermalScan model operations"""
    print("📸 Testing ThermalScan model...")
    
    try:
        db = next(get_db())
        
        # Get user and substation for foreign keys
        user = db.query(User).first()
        substation = db.query(Substation).first()
        
        if not user or not substation:
            print("❌ Missing user or substation for thermal scan test")
            return False
        
        # Create a thermal scan
        thermal_scan = ThermalScan(
            original_filename="FLIR1300.jpg",
            file_size_bytes=713248,
            file_hash="abc123def456",
            camera_model="FLIR T560",
            camera_software_version="7.22.80",
            image_width=640,
            image_height=480,
            latitude=19.1262,
            longitude=72.8897,
            capture_timestamp=datetime.now(),
            ambient_temperature=34.0,
            batch_id="batch_001",
            batch_sequence=1,
            substation_id=substation.id,
            uploaded_by=user.id
        )
        
        db.add(thermal_scan)
        db.commit()
        
        # Test status update
        thermal_scan.update_processing_status("processing")
        thermal_scan.update_processing_status("completed")
        
        print(f"✅ Thermal scan created: {thermal_scan.original_filename}")
        print(f"✅ File size: {thermal_scan.file_size_str}")
        print(f"✅ Processing time: {thermal_scan.processing_time_str}")
        return True
        
    except Exception as e:
        print(f"❌ Thermal scan model test failed: {e}")
        return False

def test_ai_analysis_model():
    """Test AI Analysis model operations"""
    print("🤖 Testing AI Analysis model...")
    
    try:
        db = next(get_db())
        
        # Get thermal scan for foreign key
        thermal_scan = db.query(ThermalScan).first()
        if not thermal_scan:
            print("❌ Missing thermal scan for AI analysis test")
            return False
        
        # Create AI analysis
        ai_analysis = AIAnalysis(
            thermal_scan_id=thermal_scan.id,
            model_version="yolo_nas_s_mobilenet_v3",
            is_good_quality=True,
            quality_score=0.85,
            ambient_temperature=34.0,
            max_temperature_detected=67.5,
            min_temperature_detected=28.0,
            avg_temperature=42.3,
            total_hotspots=3,
            critical_hotspots=1,
            potential_hotspots=2,
            normal_zones=8,
            total_components_detected=5,
            nuts_bolts_count=3,
            mid_span_joints_count=1,
            polymer_insulators_count=1,
            overall_risk_level="medium",
            risk_score=65.0,
            summary_text="Medium risk thermal signature detected with 1 critical hotspot requiring attention."
        )
        
        db.add(ai_analysis)
        db.commit()
        
        # Create a detection
        detection = Detection(
            ai_analysis_id=ai_analysis.id,
            component_type="nuts_bolts",
            confidence=0.92,
            bbox_x=0.3,
            bbox_y=0.2,
            bbox_width=0.1,
            bbox_height=0.15,
            center_x=0.35,
            center_y=0.275,
            max_temperature=67.5,
            avg_temperature=58.2,
            hotspot_classification="critical",
            temperature_above_ambient=33.5,
            risk_level="high"
        )
        
        db.add(detection)
        db.commit()
        
        print(f"✅ AI Analysis created: Risk level {ai_analysis.overall_risk_level}")
        print(f"✅ Detection summary: {ai_analysis.detection_summary}")
        print(f"✅ Hotspot summary: {ai_analysis.hotspot_summary}")
        print(f"✅ Detection created: {detection.component_type} (confidence: {detection.confidence})")
        print(f"✅ Is critical: {detection.is_critical}")
        return True
        
    except Exception as e:
        print(f"❌ AI analysis model test failed: {e}")
        return False

def main():
    """Run all database tests"""
    print("🚀 Starting Thermal Inspection Database Tests\n")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("Table Creation", create_tables),
        ("User Model", test_user_model),
        ("Substation Model", test_substation_model),
        ("Thermal Scan Model", test_thermal_scan_model),
        ("AI Analysis Model", test_ai_analysis_model)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        if test_func():
            passed += 1
        else:
            print(f"❌ {test_name} FAILED")
    
    print(f"\n{'='*50}")
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    print('='*50)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Database setup is working perfectly!")
        return True
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    main() 