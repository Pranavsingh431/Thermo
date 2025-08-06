#!/usr/bin/env python3
"""
Quick setup script - creates essential test user
"""

import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.database import SessionLocal
from app.models.user import User

def quick_setup():
    """Create just the engineer user for demo"""
    db = SessionLocal()
    
    try:
        # Check if engineer user already exists
        existing_user = db.query(User).filter(User.username == "engineer").first()
        if existing_user:
            print("✅ Engineer user already exists")
            return True
        
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
        db.commit()
        
        print("✅ Engineer user created successfully!")
        print("   Username: engineer")
        print("   Password: engineer123")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 Quick setup for demo...")
    success = quick_setup()
    if success:
        print("🎉 Ready for demo!")
    else:
        print("❌ Setup failed") 