#!/usr/bin/env python3
"""
Quick test to verify OneDrive integration is visible in the web app
Run this to test locally with mock credentials
"""

import os
import sys
from datetime import datetime

# Set up mock environment variables for testing
os.environ.setdefault('NOTED_USERNAME', 'test_user')
os.environ.setdefault('NOTED_PASSWORD_HASH', '$2b$12$example_hash_for_testing')
os.environ.setdefault('SECRET_KEY', 'test_secret_key_for_development')

def test_without_onedrive():
    """Test what happens when NOTED_CLIENT_ID is not set"""
    print("🧪 Testing WITHOUT OneDrive CLIENT_ID...")
    
    # Make sure CLIENT_ID is not set
    if 'NOTED_CLIENT_ID' in os.environ:
        del os.environ['NOTED_CLIENT_ID']
    
    try:
        # Import after clearing environment
        import importlib
        if 'onedrive_web_manager' in sys.modules:
            importlib.reload(sys.modules['onedrive_web_manager'])
        
        from onedrive_web_manager import WebOneDriveManager
        manager = WebOneDriveManager()
        print("❌ ERROR: OneDrive manager should have failed without CLIENT_ID")
        return False
    except ValueError as e:
        if "NOTED_CLIENT_ID" in str(e):
            print(f"✅ CORRECT: {e}")
            return True
        else:
            print(f"❌ WRONG ERROR: {e}")
            return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        return False

def test_with_onedrive():
    """Test what happens when NOTED_CLIENT_ID is set"""
    print("\n🧪 Testing WITH OneDrive CLIENT_ID...")
    
    # Set mock CLIENT_ID
    os.environ['NOTED_CLIENT_ID'] = 'mock-client-id-for-testing'
    
    try:
        # Reload modules to pick up new environment
        import importlib
        if 'onedrive_web_manager' in sys.modules:
            importlib.reload(sys.modules['onedrive_web_manager'])
        
        from onedrive_web_manager import WebOneDriveManager
        manager = WebOneDriveManager()
        print("✅ OneDrive manager initialized successfully")
        
        # Test status
        status = manager.get_auth_status()
        print(f"✅ Status check works: {status}")
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def test_flask_integration():
    """Test Flask app integration"""
    print("\n🧪 Testing Flask Integration...")
    
    try:
        # Test imports
        sys.path.insert(0, os.path.dirname(__file__))
        
        # Clear any cached modules
        modules_to_clear = [name for name in sys.modules.keys() if 'web-mobile-noted' in name or 'onedrive' in name]
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]
        
        # Import the web app module by file path
        import importlib.util
        spec = importlib.util.spec_from_file_location("web_mobile_noted", "web-mobile-noted.py")
        web_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(web_module)
        
        app = web_module.app
        onedrive_available = web_module.ONEDRIVE_AVAILABLE
        onedrive_manager = web_module.onedrive_manager
        
        print(f"✅ Flask app loaded: {app}")
        print(f"✅ OneDrive available: {onedrive_available}")
        print(f"✅ OneDrive manager: {onedrive_manager is not None}")
        
        # Test with app context
        with app.app_context():
            print("✅ App context works")
        
        return True
        
    except Exception as e:
        print(f"❌ Flask integration error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 OneDrive Integration Test")
    print("=" * 50)
    
    results = []
    results.append(test_without_onedrive())
    results.append(test_with_onedrive())
    results.append(test_flask_integration())
    
    print("\n" + "=" * 50)
    print(f"📊 Results: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("🎉 All tests passed! OneDrive integration is ready.")
        print("\n📋 Next steps for Railway deployment:")
        print("1. Set NOTED_CLIENT_ID environment variable")
        print("2. Deploy updated code")
        print("3. Look for OneDrive button (☁️) in web app")
    else:
        print("❌ Some tests failed. Check the errors above.")
        sys.exit(1)