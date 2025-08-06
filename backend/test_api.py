#!/usr/bin/env python3
"""
Test script for Thermal Inspection API
"""

import sys
import os
import requests
import json
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test API health check"""
    print("🔍 Testing API health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API Health: {data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_root_endpoint():
    """Test root endpoint"""
    print("🔍 Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Root endpoint: {data}")
            return True
        else:
            print(f"❌ Root endpoint failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Root endpoint error: {e}")
        return False

def test_docs_endpoint():
    """Test API documentation"""
    print("🔍 Testing API docs...")
    try:
        response = requests.get(f"{BASE_URL}/api/docs")
        if response.status_code == 200:
            print("✅ API documentation accessible")
            return True
        else:
            print(f"❌ API docs failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API docs error: {e}")
        return False

def test_auth_endpoints():
    """Test authentication endpoints"""
    print("🔍 Testing authentication endpoints...")
    try:
        # Test auth health check
        response = requests.get(f"{BASE_URL}/api/auth/health")
        if response.status_code == 200:
            print("✅ Auth service healthy")
        else:
            print(f"❌ Auth health check failed: {response.status_code}")
            return False
        
        # Test login endpoint (should fail without credentials)
        response = requests.post(f"{BASE_URL}/api/auth/login", data={
            "username": "nonexistent",
            "password": "wrong"
        })
        if response.status_code == 401:
            print("✅ Login properly rejects invalid credentials")
            return True
        else:
            print(f"❌ Login endpoint unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Auth endpoints error: {e}")
        return False

def test_upload_endpoints():
    """Test upload endpoints (without authentication)"""
    print("🔍 Testing upload endpoints...")
    try:
        # Test upload health check
        response = requests.get(f"{BASE_URL}/api/upload/health")
        if response.status_code == 200:
            print("✅ Upload service healthy")
        
        # Test protected upload endpoint (should require auth)
        response = requests.post(f"{BASE_URL}/api/upload/thermal-images")
        if response.status_code == 401:
            print("✅ Upload endpoint properly requires authentication")
            return True
        else:
            print(f"❌ Upload endpoint unexpected response: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Upload endpoints error: {e}")
        return False

def main():
    """Run all API tests"""
    print("🚀 Starting Thermal Inspection API Tests\n")
    
    tests = [
        ("Root Endpoint", test_root_endpoint),
        ("Health Check", test_health_check),
        ("API Documentation", test_docs_endpoint),
        ("Authentication Endpoints", test_auth_endpoints),
        ("Upload Endpoints", test_upload_endpoints)
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
    print(f"API TEST RESULTS: {passed}/{total} tests passed")
    print('='*50)
    
    if passed == total:
        print("🎉 ALL API TESTS PASSED! Backend is working correctly!")
        print(f"📊 API Documentation: {BASE_URL}/api/docs")
        print(f"🔧 API Health: {BASE_URL}/health")
        return True
    else:
        print("⚠️ Some API tests failed. Check the server is running:")
        print(f"🚀 Start server: cd backend && python3 -m uvicorn app.main:app --reload")
        return False

if __name__ == "__main__":
    main() 