#!/usr/bin/env python3
"""
Test Railway timeout resilience improvements
"""
import os
import sys
import json

# Set UTF-8 encoding
os.environ['PYTHONIOENCODING'] = 'utf-8'

try:
    # Import web app module
    import importlib.util
    spec = importlib.util.spec_from_file_location("web_mobile_noted", "web-mobile-noted.py")
    if spec is None or spec.loader is None:
        raise ImportError("Could not load web-mobile-noted.py")
    wmn = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wmn)
    
    app = wmn.app
    
    print("✅ Testing Railway timeout resilience improvements")
    print(f"OneDrive available: {wmn.ONEDRIVE_AVAILABLE}")
    print(f"OneDrive manager: {wmn.onedrive_manager is not None}")
    
    # Test the endpoints that were timing out
    with app.test_client() as client:
        print("\n🔍 Testing endpoint response times...")
        
        import time
        
        # Test simple OneDrive status
        start_time = time.time()
        response = client.get('/api/simple/onedrive/status')
        end_time = time.time()
        print(f"⏱️ Status endpoint: {end_time - start_time:.2f}s (Status: {response.status_code})")
        
        # Test auth check endpoint  
        start_time = time.time()
        response = client.get('/api/simple/onedrive/auth/check')
        end_time = time.time()
        print(f"⏱️ Auth check endpoint: {end_time - start_time:.2f}s (Status: {response.status_code})")
        
        # Simulate starting auth flow
        start_time = time.time()
        response = client.post('/api/simple/onedrive/auth/start', 
                             headers={'Content-Type': 'application/json'}, 
                             json={})
        end_time = time.time()
        print(f"⏱️ Auth start endpoint: {end_time - start_time:.2f}s (Status: {response.status_code})")
        
        if response.status_code == 200:
            data = response.get_json()
            if data.get('success'):
                print("✅ Auth flow started successfully")
            else:
                print(f"❌ Auth flow failed: {data}")
    
    print("\n🎉 Railway Timeout Resilience Summary:")
    print("- Increased OneDrive status timeout: 20s → 60s") 
    print("- Increased retry timeout: 30s → 90s")
    print("- Increased auth progress timeout: 15s → 45s")
    print("- Added 'not_found' auth flow recovery handling")
    print("- Added timeout retry counter (max 5 attempts)")
    print("- Increased retry delay: 10s → 20s")
    print("- Railway deployment should handle server load better")
        
except Exception as e:
    print(f"❌ Error testing timeout resilience: {e}")
    import traceback
    traceback.print_exc()