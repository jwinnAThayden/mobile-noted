#!/usr/bin/env python3
"""
Test OneDrive authentication with alternative MSAL configuration.
Try different approaches to resolve the ID token audience error.
"""

import os
import msal

# Use the correct configuration
CLIENT_ID = "cf7bb4c5-7271-4caf-adb3-f8f1f1bef9d5"
AUTHORITY = "https://login.microsoftonline.com/5834cf33-1f0f-463a-9150-b123cae25d8d"
SCOPES = ["Files.ReadWrite.AppFolder", "User.Read"]

def test_alternative_approaches():
    print("=== Testing Alternative MSAL Approaches ===")
    print(f"CLIENT_ID: {CLIENT_ID}")
    print(f"AUTHORITY: {AUTHORITY}")
    print(f"SCOPES: {SCOPES}")
    
    # Approach 1: Try with validate_authority=False
    try:
        print("\n🔄 Approach 1: PublicClientApplication with validate_authority=False")
        app1 = msal.PublicClientApplication(
            CLIENT_ID,
            authority=AUTHORITY,
            validate_authority=False,
            token_cache=None
        )
        
        flow = app1.initiate_device_flow(scopes=SCOPES)
        if "user_code" in flow:
            print(f"✅ Device flow initiated successfully")
            print(f"📱 Go to: {flow['verification_uri']}")
            print(f"🔑 Enter code: {flow['user_code']}")
            
            # Try completing authentication with this approach
            response = input("\nComplete authentication with Approach 1? (y/n): ")
            if response.lower() == 'y':
                result = app1.acquire_token_by_device_flow(flow)
                if result and "access_token" in result:
                    print("✅ Approach 1 SUCCESS!")
                    return True
                else:
                    print(f"❌ Approach 1 failed: {result}")
        else:
            print(f"❌ Approach 1 device flow failed")
            
    except Exception as e:
        print(f"❌ Approach 1 exception: {e}")
    
    # Approach 2: Try with no token cache and different settings
    try:
        print("\n🔄 Approach 2: Minimal configuration")
        app2 = msal.PublicClientApplication(
            CLIENT_ID.strip(),  # Ensure no whitespace
            authority=AUTHORITY,
            token_cache=None
        )
        
        # Use alternative scopes configuration
        minimal_scopes = ["https://graph.microsoft.com/Files.ReadWrite.AppFolder"]
        
        flow = app2.initiate_device_flow(scopes=minimal_scopes)
        if "user_code" in flow:
            print(f"✅ Device flow initiated with minimal scopes")
            print(f"📱 Go to: {flow['verification_uri']}")
            print(f"🔑 Enter code: {flow['user_code']}")
            
            response = input("\nComplete authentication with Approach 2? (y/n): ")
            if response.lower() == 'y':
                result = app2.acquire_token_by_device_flow(flow)
                if result and "access_token" in result:
                    print("✅ Approach 2 SUCCESS!")
                    return True
                else:
                    print(f"❌ Approach 2 failed: {result}")
        else:
            print(f"❌ Approach 2 device flow failed")
            
    except Exception as e:
        print(f"❌ Approach 2 exception: {e}")
    
    # Approach 3: Try with /common authority instead of tenant-specific
    try:
        print("\n🔄 Approach 3: Using /common authority")
        app3 = msal.PublicClientApplication(
            CLIENT_ID,
            authority="https://login.microsoftonline.com/common",
            token_cache=None
        )
        
        flow = app3.initiate_device_flow(scopes=SCOPES)
        if "user_code" in flow:
            print(f"✅ Device flow initiated with /common")
            print(f"📱 Go to: {flow['verification_uri']}")
            print(f"🔑 Enter code: {flow['user_code']}")
            
            response = input("\nComplete authentication with Approach 3? (y/n): ")
            if response.lower() == 'y':
                result = app3.acquire_token_by_device_flow(flow)
                if result and "access_token" in result:
                    print("✅ Approach 3 SUCCESS!")
                    return True
                else:
                    print(f"❌ Approach 3 failed: {result}")
        else:
            print(f"❌ Approach 3 device flow failed")
            
    except Exception as e:
        print(f"❌ Approach 3 exception: {e}")
    
    print("\n❌ All approaches failed")
    return False

if __name__ == "__main__":
    success = test_alternative_approaches()
    
    if success:
        print("\n🎉 Found a working authentication approach!")
    else:
        print("\n💡 Consider checking the Azure app registration:")
        print("   1. Go to https://portal.azure.com")
        print("   2. Azure Active Directory → App registrations")  
        print("   3. Find your app: cf7bb4c5-7271-4caf-adb3-f8f1f1bef9d5")
        print("   4. Authentication → Advanced settings → Allow public client flows: YES")
        print("   5. Authentication → Supported account types: Check settings")