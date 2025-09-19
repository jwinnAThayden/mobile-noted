#!/usr/bin/env python3
"""
Test OneDrive authentication to debug device flow issues.
"""

import os
from onedrive_manager import OneDriveManager

def test_onedrive_auth():
    print("=== OneDrive Authentication Test ===")
    
    # Check CLIENT_ID
    client_id = os.environ.get('NOTED_CLIENT_ID')
    if client_id:
        print(f"CLIENT_ID: {client_id[:10]}...{client_id[-4:]}")
    else:
        print("CLIENT_ID: NOT SET")
    
    if not client_id:
        print("ERROR: NOTED_CLIENT_ID environment variable not set!")
        print("Run: set NOTED_CLIENT_ID=cf7bb4c5-6b32-4dc1-b1e4-60bb89b11335f")
        return
    
    # Test OneDrive manager initialization
    try:
        print("\n1. Initializing OneDrive Manager...")
        manager = OneDriveManager()
        print("   ✅ OneDrive Manager initialized successfully")
    except Exception as e:
        print(f"   ❌ Failed to initialize OneDrive Manager: {e}")
        return
    
    # Test authentication
    try:
        print("\n2. Testing authentication...")
        success, message = manager.authenticate()
        
        if success:
            print(f"   ✅ Authentication successful: {message}")
            
            # Test user info
            try:
                user_info = manager.get_user_info()
                if user_info:
                    print(f"   User: {user_info.get('displayName', 'Unknown')} ({user_info.get('mail', 'No email')})")
                else:
                    print("   ⚠️  No user info returned")
            except Exception as e:
                print(f"   ⚠️  Could not get user info: {e}")
                
        else:
            print(f"   ❌ Authentication failed: {message}")
            
    except Exception as e:
        print(f"   ❌ Exception during authentication: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_onedrive_auth()