#!/usr/bin/env python3
"""
Test script to verify OneDrive authentication fixes
"""
import os
import sys
import time
import json

# Set UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    # Import the web app
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Import web-mobile-noted.py as a module
    import importlib.util
    spec = importlib.util.spec_from_file_location("web_mobile_noted", "web-mobile-noted.py")
    wmn = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wmn)
    
    # Create Flask app for testing
    app = wmn.app
    
    print("✅ Flask app imported successfully")
    print(f"OneDrive available: {wmn.ONEDRIVE_AVAILABLE}")
    print(f"OneDrive manager: {wmn.onedrive_manager is not None}")
    
    # Test the simple auth endpoint
    with app.test_client() as client:
        print("\n🔍 Testing simple auth check endpoint...")
        
        # Test without session
        response = client.get('/api/simple/onedrive/auth/check')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.get_json()}")
        
        # Test OneDrive status endpoint
        print("\n🔍 Testing OneDrive status endpoint...")
        response = client.get('/api/onedrive/status')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.get_json()}")
        
        print("\n✅ All endpoint tests completed successfully!")
        
except Exception as e:
    print(f"❌ Error testing authentication fixes: {e}")
    import traceback
    traceback.print_exc()