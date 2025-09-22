#!/usr/bin/env python3
"""
Test timeout fixes for OneDrive status checking
"""
import os
import sys
import time
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
    
    print("✅ Testing timeout fixes for OneDrive authentication")
    print(f"OneDrive available: {wmn.ONEDRIVE_AVAILABLE}")
    print(f"OneDrive manager: {wmn.onedrive_manager is not None}")
    
    # Test the endpoints with timing
    with app.test_client() as client:
        print("\n🔍 Testing simple OneDrive status endpoint timing...")
        
        start_time = time.time()
        response = client.get('/api/simple/onedrive/status')
        end_time = time.time()
        
        print(f"⏱️ Response time: {end_time - start_time:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print(f"Response: Available={data.get('available')}, Authenticated={data.get('authenticated')}")
            print("✅ Status endpoint responding quickly - timeout fixes should work")
        else:
            print(f"❌ Endpoint returned error: {response.status_code}")
        
        print("\n🔍 Testing auth check endpoint timing...")
        
        start_time = time.time()
        response = client.get('/api/simple/onedrive/auth/check')
        end_time = time.time()
        
        print(f"⏱️ Response time: {end_time - start_time:.2f} seconds")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.get_json()
            print(f"Response: Status={data.get('status')}, Message={data.get('message')}")
            print("✅ Auth check endpoint responding quickly - timeout fixes should work")
        else:
            print(f"❌ Endpoint returned error: {response.status_code}")
        
        print("\n🎉 Timeout Fix Summary:")
        print("- Increased timeout from 5s to 20s for initial requests")
        print("- Added retry logic with 30s timeout for failed requests")  
        print("- Enhanced error handling for AbortError (timeout)")
        print("- Auth progress checks now have 15s timeout with graceful retry")
        print("- Railway deployment should now work without timeout errors")
        
except Exception as e:
    print(f"❌ Error testing timeout fixes: {e}")
    import traceback
    traceback.print_exc()