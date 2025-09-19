#!/usr/bin/env python3
"""
Test different authority configurations to identify the correct tenant.
"""

import os
import msal

def test_authorities():
    client_id = os.environ.get('NOTED_CLIENT_ID')
    if not client_id:
        print("ERROR: NOTED_CLIENT_ID not set")
        return
        
    print(f"Testing with CLIENT_ID: {client_id[:10]}...{client_id[-4:]}")
    
    # Test different authority configurations
    authorities = [
        "https://login.microsoftonline.com/common",
        "https://login.microsoftonline.com/organizations", 
        "https://login.microsoftonline.com/consumers",
        # Try a specific tenant that might be associated with Hayden Beverage
        # We'll need to determine this from the user's organization
    ]
    
    scopes = ["Files.ReadWrite.AppFolder", "User.Read"]
    
    for authority in authorities:
        print(f"\n=== Testing authority: {authority} ===")
        
        try:
            app = msal.PublicClientApplication(
                client_id,
                authority=authority,
                token_cache=None
            )
            
            flow = app.initiate_device_flow(scopes=scopes)
            
            if "user_code" in flow:
                print(f"✅ SUCCESS! Device flow initiated successfully")
                print(f"   Verification URI: {flow.get('verification_uri', 'N/A')}")
                print(f"   User code: {flow.get('user_code', 'N/A')}")
                print(f"   Message: {flow.get('message', 'N/A')}")
                break
            else:
                error = flow.get('error', 'Unknown error')
                error_desc = flow.get('error_description', 'No description')
                print(f"❌ FAILED: {error} - {error_desc[:100]}...")
                
        except Exception as e:
            print(f"❌ EXCEPTION: {str(e)[:100]}...")

if __name__ == "__main__":
    test_authorities()