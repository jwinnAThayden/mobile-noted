#!/usr/bin/env python3
"""
Test environment variable configuration
"""

import os

def test_env_vars():
    """Test if required environment variables are set"""
    
    print("🔍 Testing Environment Variables...")
    print(f"PORT: {os.environ.get('PORT', 'Not Set')}")
    print(f"NOTED_USERNAME: {os.environ.get('NOTED_USERNAME', 'Not Set')}")
    
    # Don't print the actual password hash for security
    password_hash = os.environ.get('NOTED_PASSWORD_HASH')
    if password_hash:
        print(f"NOTED_PASSWORD_HASH: {password_hash[:20]}... (truncated)")
    else:
        print("NOTED_PASSWORD_HASH: Not Set")
    
    # Test if web-mobile-noted.py can be imported
    print("\n🔍 Testing Module Import...")
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("web_mobile_noted", "web-mobile-noted.py")
        if spec and spec.loader:
            web_mobile_noted = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(web_mobile_noted)
            print("✅ web-mobile-noted.py imported successfully")
            print(f"✅ Flask app object: {web_mobile_noted.app}")
        else:
            print("❌ Could not create module spec")
    except Exception as e:
        print(f"❌ Import error: {e}")

if __name__ == "__main__":
    test_env_vars()