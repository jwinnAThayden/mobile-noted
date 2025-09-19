#!/usr/bin/env python3
"""
Test OneDrive authentication using the exact same configuration as the web version.
"""

import os
import msal

def test_web_config():
    print("=== Testing with Web OneDrive Configuration ===")
    
    # Use EXACT same config as web version
    CLIENT_ID = os.environ.get("NOTED_CLIENT_ID")
    AUTHORITY = "https://login.microsoftonline.com/common"
    SCOPES = ["Files.ReadWrite.AppFolder", "User.Read"]  # No offline_access like web version
    
    if not CLIENT_ID:
        print("ERROR: NOTED_CLIENT_ID not set")
        return
        
    print(f"CLIENT_ID: {CLIENT_ID[:10]}...{CLIENT_ID[-4:]}")
    print(f"AUTHORITY: {AUTHORITY}")
    print(f"SCOPES: {SCOPES}")
    
    try:
        # Create the MSAL app exactly like the desktop version
        app = msal.PublicClientApplication(
            CLIENT_ID,
            authority=AUTHORITY,
            token_cache=None
        )
        print("✅ MSAL Public Client Application created")
        
        # Try device flow like desktop version
        print("\n🔄 Initiating device flow...")
        flow = app.initiate_device_flow(scopes=SCOPES)
        
        print(f"Flow response keys: {list(flow.keys())}")
        
        if "user_code" in flow:
            print("✅ SUCCESS! Device flow initiated")
            print(f"📱 Go to: {flow['verification_uri']}")
            print(f"🔑 Enter code: {flow['user_code']}")
            print(f"⏰ Expires in: {flow.get('expires_in', 'unknown')} seconds")
            
            # Ask user if they want to complete the flow
            response = input("\nDo you want to complete the authentication? (y/n): ")
            if response.lower() == 'y':
                print("\n🔄 Waiting for authentication...")
                result = app.acquire_token_by_device_flow(flow)
                
                if result and "access_token" in result:
                    print("✅ Authentication successful!")
                    print(f"Token type: {result.get('token_type', 'unknown')}")
                    print(f"Scope: {result.get('scope', 'unknown')}")
                    return True
                else:
                    print(f"❌ Authentication failed: {result}")
                    return False
            else:
                print("ℹ️  Authentication skipped by user")
                return None
                
        else:
            error = flow.get('error', 'Unknown error')
            error_desc = flow.get('error_description', 'No description')
            print(f"❌ Device flow failed: {error}")
            print(f"   Description: {error_desc}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_web_config()