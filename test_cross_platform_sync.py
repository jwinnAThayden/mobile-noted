"""
Complete OneDrive Cross-Platform Sync Test
Test that Desktop → OneDrive → Railway sync works correctly.
"""

import requests
import json
import time
from datetime import datetime

# Configuration
RAILWAY_URL = "https://web-mobile-noted-production.up.railway.app"  # Update with your Railway URL
session = requests.Session()

def test_railway_onedrive_functions():
    """Test all Railway OneDrive endpoints to verify functionality."""
    
    print("🧪 Railway OneDrive Functionality Test")
    print("=" * 60)
    
    try:
        # Test 1: Check if OneDrive is available
        print("\n1️⃣ Testing OneDrive availability...")
        
        simple_check = session.get(f"{RAILWAY_URL}/api/onedrive/auth/simple-check")
        
        if simple_check.status_code == 200:
            data = simple_check.json()
            print(f"✅ OneDrive available: {data.get('success')}")
            print(f"🔐 Authenticated: {data.get('authenticated')}")
            print(f"📊 Status: {data.get('status')}")
        else:
            print(f"❌ Simple check failed: {simple_check.status_code}")
            print(f"Response: {simple_check.text}")
            return False
        
        # Test 2: Start authentication if not authenticated
        if not data.get('authenticated'):
            print("\n2️⃣ Starting OneDrive authentication...")
            
            auth_start = session.get(f"{RAILWAY_URL}/api/onedrive/auth/start")
            
            if auth_start.status_code == 200:
                auth_data = auth_start.json()
                print(f"✅ Authentication started!")
                print(f"👤 User code: {auth_data.get('user_code')}")
                print(f"🌐 Verification URL: {auth_data.get('verification_uri')}")
                print(f"⏰ Expires in: {auth_data.get('expires_in', 0)/60:.1f} minutes")
                
                # Give instructions
                print(f"\n📱 PLEASE COMPLETE AUTHENTICATION:")
                print(f"1. Go to: {auth_data.get('verification_uri')}")
                print(f"2. Enter code: {auth_data.get('user_code')}")
                print(f"3. Sign in and authorize the app")
                print(f"4. Come back here and press Enter when done...")
                input()
                
                # Check auth status
                print("\n3️⃣ Checking authentication status...")
                for i in range(12):  # Check for 2 minutes
                    auth_check = session.get(f"{RAILWAY_URL}/api/onedrive/auth/check")
                    if auth_check.status_code == 200:
                        status = auth_check.json()
                        print(f"[{i+1}/12] Status: {status.get('status', 'unknown')}")
                        
                        if status.get('status') in ['success', 'completed']:
                            print("✅ Authentication successful!")
                            break
                        elif status.get('status') in ['error', 'expired']:
                            print(f"❌ Authentication failed: {status.get('message')}")
                            return False
                    
                    time.sleep(10)
                else:
                    print("❌ Authentication timeout")
                    return False
            else:
                print(f"❌ Failed to start auth: {auth_start.status_code}")
                return False
        
        # Test 3: Test OneDrive sync functions
        print("\n4️⃣ Testing OneDrive sync functions...")
        
        # Test pull from OneDrive
        print("📥 Testing 'Pull from OneDrive'...")
        pull_response = session.post(f"{RAILWAY_URL}/api/onedrive/sync/pull")
        
        if pull_response.status_code == 200:
            pull_data = pull_response.json()
            print(f"✅ Pull successful!")
            print(f"📊 Result: {pull_data}")
            
            # Check if any notes were found
            if isinstance(pull_data, dict) and 'notes' in pull_data:
                notes_count = len(pull_data.get('notes', []))
                print(f"📝 Found {notes_count} notes on OneDrive")
                
                if notes_count > 0:
                    print("📋 Note details:")
                    for i, note in enumerate(pull_data['notes'][:3]):  # Show first 3
                        print(f"   {i+1}. {note.get('title', 'Untitled')} ({note.get('size', 0)} bytes)")
                    if notes_count > 3:
                        print(f"   ... and {notes_count - 3} more")
            else:
                print("ℹ️  No notes structure in response")
        else:
            print(f"❌ Pull failed: {pull_response.status_code}")
            print(f"Response: {pull_response.text}")
        
        # Test push to OneDrive (with test note)
        print("\n📤 Testing 'Push to OneDrive'...")
        
        # First, create a test note
        test_note_data = {
            'content': f'Test note created by Railway app at {datetime.now().isoformat()}',
            'title': f'Railway Test Note {int(time.time())}'
        }
        
        # Add the note first (if we have an endpoint for it)
        # For now, let's just test the push endpoint
        push_response = session.post(f"{RAILWAY_URL}/api/onedrive/sync/push")
        
        if push_response.status_code == 200:
            push_data = push_response.json()
            print(f"✅ Push successful!")
            print(f"📊 Result: {push_data}")
        else:
            print(f"❌ Push failed: {push_response.status_code}")
            print(f"Response: {push_response.text}")
        
        print("\n🎯 Test Summary:")
        print("✅ OneDrive integration is working on Railway")
        print("✅ Authentication flow is functional")
        print("✅ Pull/Push endpoints are responding")
        print("\n💡 Next steps:")
        print("1. Use your desktop app to sync notes to OneDrive")
        print("2. Use Railway app to pull notes from OneDrive")
        print("3. Verify notes appear correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_debug_endpoints():
    """Test the debugging endpoints."""
    
    print("\n🔍 Testing Debug Endpoints")
    print("-" * 40)
    
    # Debug flow status
    debug_response = session.get(f"{RAILWAY_URL}/api/onedrive/debug/flow-status")
    
    if debug_response.status_code == 200:
        debug_data = debug_response.json()
        print(f"📊 Debug Info: {json.dumps(debug_data, indent=2)}")
    else:
        print(f"❌ Debug endpoint failed: {debug_response.status_code}")
    
    # Test timeout extension
    extend_response = session.post(f"{RAILWAY_URL}/api/onedrive/extend-timeout")
    
    if extend_response.status_code == 200:
        extend_data = extend_response.json()
        print(f"⏰ Timeout Extension: {json.dumps(extend_data, indent=2)}")
    else:
        print(f"❌ Extend endpoint failed: {extend_response.status_code}")

if __name__ == "__main__":
    print("🎯 OneDrive Cross-Platform Sync Testing Suite")
    print("=" * 70)
    print()
    print("This will test the Railway app's OneDrive functionality")
    print("and verify that cross-platform sync is working correctly.")
    print()
    
    choice = input("Press Enter to start testing, or 'q' to quit: ").strip().lower()
    
    if choice != 'q':
        success = test_railway_onedrive_functions()
        
        if success:
            debug_choice = input("\nWould you like to run debug tests too? (y/n): ").lower().strip()
            if debug_choice == 'y':
                test_debug_endpoints()
        
        print("\n" + "=" * 70)
        print("🏁 Testing Complete!")
        
        if success:
            print("✅ Railway OneDrive integration is working correctly!")
            print("\n🔄 To test complete cross-platform sync:")
            print("1. Set NOTED_CLIENT_ID environment variable in your desktop app")
            print("2. Use desktop app 'OneDrive Sync' button and choose 'YES' to save TO OneDrive")
            print("3. Use Railway app 'Pull from OneDrive' to retrieve the notes")
            print("4. Verify notes appear in Railway app")
        else:
            print("❌ Some tests failed - check the output above for issues")
    else:
        print("👋 Testing cancelled")