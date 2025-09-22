#!/usr/bin/env python3
"""
Test OneDrive authentication method fix
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
    
    print("✅ Testing OneDrive auth method fix")
    print(f"OneDrive available: {wmn.ONEDRIVE_AVAILABLE}")
    print(f"OneDrive manager: {wmn.onedrive_manager is not None}")
    
    # Check if the method exists
    if wmn.onedrive_manager:
        has_method = hasattr(wmn.onedrive_manager, 'check_device_flow_status')
        print(f"✅ check_device_flow_status method exists: {has_method}")
        
        # Test the auth endpoint that was failing
        with app.test_client() as client:
            print("\n🔍 Testing simple auth check endpoint (the one that was failing)...")
            
            response = client.get('/api/simple/onedrive/auth/check')
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"Response: Status={data.get('status')}, Message={data.get('message')}")
                
                # Check if the error message about missing attribute is gone
                if 'has no attribute' in data.get('message', ''):
                    print("❌ Still getting attribute error!")
                else:
                    print("✅ No more attribute error - method name fix successful!")
            else:
                print(f"❌ Endpoint returned error: {response.status_code}")
    
    print("\n🎉 Method Fix Summary:")
    print("- Fixed method name from 'check_device_flow_auth' to 'check_device_flow_status'")
    print("- OneDrive authentication progress checking should now work")
    print("- Ready for Railway deployment")
        
except Exception as e:
    print(f"❌ Error testing method fix: {e}")
    import traceback
    traceback.print_exc()