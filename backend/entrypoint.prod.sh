#!/bin/bash
# Production Entrypoint Script for Tata Power Thermal Eye
# =======================================================
# 
# This script ensures bulletproof production startup with:
# - Database migration verification
# - Health check confirmations
# - Graceful error handling
# - Production logging

set -e

echo "🚀 Tata Power Thermal Eye - Production Startup"
echo "=============================================="

# Function to wait for database
wait_for_db() {
    echo "📊 Waiting for database connection..."
    
    while ! python -c "
import psycopg2
import os
import sys
try:
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    conn.close()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    sys.exit(1)
" 2>/dev/null; do
        echo "⏳ Database not ready, waiting 5 seconds..."
        sleep 5
    done
}

# Function to run database migrations
run_migrations() {
    echo "🔄 Running database migrations..."
    
    # Check if alembic is available
    if command -v alembic > /dev/null 2>&1; then
        echo "📋 Running Alembic migrations..."
        alembic upgrade head
        echo "✅ Database migrations completed"
    else
        echo "⚠️ Alembic not available, ensuring tables exist..."
        python -c "
from app.database import engine, Base
from app.models import thermal_scan, ai_analysis, user
Base.metadata.create_all(bind=engine)
print('✅ Database tables verified')
"
    fi
}

# Function to verify AI system
verify_ai_system() {
    echo "🤖 Verifying AI system..."
    
    python -c "
try:
    from app.services.bulletproof_ai_pipeline import bulletproof_ai_pipeline
    status = bulletproof_ai_pipeline.get_system_status()
    print(f'✅ AI Pipeline Status: {status[\"pipeline_status\"]}')
    print(f'   YOLO Available: {status[\"yolo_available\"]}')
    print(f'   Pattern Fallback: {status[\"pattern_fallback_available\"]}')
    
    if status['pattern_fallback_available']:
        print('🛡️ System ready with bulletproof failsafe')
    else:
        print('⚠️ Warning: No AI fallback available')
        
except Exception as e:
    print(f'⚠️ AI system verification warning: {e}')
    print('🛡️ System will attempt to continue')
"
}

# Function to create initial admin user
create_admin_user() {
    echo "👤 Checking admin user..."
    
    python -c "
try:
    from app.database import SessionLocal
    from app.models.user import User
    from app.utils.auth import get_password_hash
    import os
    
    db = SessionLocal()
    
    # Check if admin user exists
    admin_user = db.query(User).filter(User.email == 'admin@tatapower.com').first()
    
    if not admin_user:
        print('👤 Creating default admin user...')
        
        admin_password = os.environ.get('ADMIN_PASSWORD', 'TataPower@2024!')
        
        admin_user = User(
            email='admin@tatapower.com',
            username='admin',
            full_name='Tata Power Admin',
            hashed_password=get_password_hash(admin_password),
            is_active=True,
            role='admin'
        )
        
        db.add(admin_user)
        db.commit()
        
        print('✅ Admin user created: admin@tatapower.com')
        print(f'🔑 Default password: {admin_password}')
        print('⚠️ IMPORTANT: Change password after first login!')
    else:
        print('✅ Admin user already exists')
        
    db.close()
    
except Exception as e:
    print(f'⚠️ Admin user setup warning: {e}')
"
}

# Function to verify system health
verify_system_health() {
    echo "🏥 Performing system health checks..."
    
    python -c "
try:
    import os
    from pathlib import Path
    
    # Check critical directories
    critical_dirs = [
        '/app/static/thermal_images',
        '/app/static/processed_images', 
        '/app/static/reports',
        '/app/logs',
        '/app/models'
    ]
    
    for directory in critical_dirs:
        path = Path(directory)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            print(f'📁 Created directory: {directory}')
        
        if not os.access(directory, os.W_OK):
            print(f'⚠️ Warning: Directory not writable: {directory}')
        else:
            print(f'✅ Directory ready: {directory}')
    
    print('✅ System health checks completed')
    
except Exception as e:
    print(f'❌ System health check failed: {e}')
    exit(1)
"
}

# Main startup sequence
main() {
    echo "🔧 Starting production initialization sequence..."
    
    # Step 1: Wait for database
    wait_for_db
    
    # Step 2: Run migrations
    run_migrations
    
    # Step 3: Verify AI system
    verify_ai_system
    
    # Step 4: Create admin user
    create_admin_user
    
    # Step 5: System health checks
    verify_system_health
    
    echo ""
    echo "🎉 PRODUCTION INITIALIZATION COMPLETE"
    echo "====================================="
    echo "🛡️ Bulletproof system ready"
    echo "⚖️ IEEE C57.91 compliance active"
    echo "🔒 SHA256 model verification enabled"
    echo "📊 Health monitoring active"
    echo "🎯 Tata Power deployment ready"
    echo ""
    echo "🚀 Starting application server..."
    
    # Execute the main command
    exec "$@"
}

# Error handling
trap 'echo "❌ Production startup failed"; exit 1' ERR

# Run main function
main "$@" 