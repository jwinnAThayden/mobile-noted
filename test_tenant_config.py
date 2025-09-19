#!/usr/bin/env python3
"""
Test OneDrive authentication with the updated configuration (tenant-specific).
"""

import os
import msal

# Use the updated configuration directly
CLIENT_ID = "cf7bb4c5-7271-4caf-adb3-f8f1f1bef9d5"
AUTHORITY = "https://login.microsoftonline.com/5834cf33-1f0f-463a-9150-b123cae25d8d"
SCOPES = ["Files.ReadWrite.AppFolder", "User.Read"]

def test_tenant_config():
    print("=== Testing with Tenant-Specific OneDrive Configuration ===")
    print(f"CLIENT_ID: {CLIENT_ID[:10]}...{CLIENT_ID[-4:]}")
    print(f"AUTHORITY: {AUTHORITY}")
    print(f"SCOPES: {SCOPES}")
    
    try:
        # Create the MSAL app with tenant-specific authority
        app = msal.PublicClientApplication(
            CLIENT_ID,
            authority=AUTHORITY,
            token_cache=None
        )
        print("✅ MSAL Public Client Application created with tenant authority")
        
        # Try device flow
        print("\n🔄 Initiating device flow with tenant authority...")
        flow = app.initiate_device_flow(scopes=SCOPES)
        
        print(f"Flow response keys: {list(flow.keys())}")
        
        if "user_code" in flow:
            print("✅ SUCCESS! Device flow initiated with tenant authority")
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
                    
                    # Save token to demonstrate it works
                    print(f"Access token (first 20 chars): {result.get('access_token', '')[:20]}...")
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
    success = test_tenant_config()
    
    if success:
        print("\n🎉 OneDrive authentication is working!")
        print("You can now use OneDrive sync in your desktop app!")
    elif success is False:
        print("\n❌ OneDrive authentication failed")
    else:
        print("\n⏸️  Authentication test skipped")