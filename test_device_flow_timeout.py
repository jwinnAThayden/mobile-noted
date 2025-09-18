"""
OneDrive Device Flow Timeout Testing Script
Use this to test and debug the device flow authentication timeout issues.
"""

import requests
import time
import json

# Configuration
RAILWAY_URL = "https://web-mobile-noted-production.up.railway.app"  # Update with your actual Railway URL
session = requests.Session()

def test_device_flow_timeout():
    """Test the device flow authentication with extended timeout."""
    
    print("🧪 OneDrive Device Flow Timeout Test")
    print("=" * 50)
    
    try:
        # Step 1: Start authentication
        print("1️⃣ Starting device flow authentication...")
        
        auth_response = session.get(f"{RAILWAY_URL}/api/onedrive/auth/start")
        
        if auth_response.status_code != 200:
            print(f"❌ Failed to start auth: {auth_response.status_code}")
            print(f"Response: {auth_response.text}")
            return
        
        auth_data = auth_response.json()
        print(f"✅ Auth started successfully!")
        print(f"👤 User code: {auth_data.get('user_code')}")
        print(f"🌐 Verification URL: {auth_data.get('verification_uri')}")
        print(f"⏰ Expires in: {auth_data.get('expires_in', 0)/60:.1f} minutes")
        print()
        
        # Step 2: Check debug status
        print("2️⃣ Checking debug flow status...")
        
        debug_response = session.get(f"{RAILWAY_URL}/api/onedrive/debug/flow-status")
        
        if debug_response.status_code == 200:
            debug_data = debug_response.json()
            if debug_data.get('success'):
                print(f"✅ Debug info retrieved:")
                print(f"⏱️  Elapsed: {debug_data.get('elapsed_minutes', 0):.1f} minutes")
                print(f"⏰ Timeout: {debug_data.get('timeout_minutes', 0):.1f} minutes")
                print(f"⏳ Remaining: {debug_data.get('time_remaining_minutes', 0):.1f} minutes")
                print(f"📊 Original timeout: {debug_data.get('original_timeout', 'unknown')} seconds")
                print(f"📊 Extended timeout: {debug_data.get('extended_timeout', 'unknown')} seconds")
            else:
                print(f"❌ Debug failed: {debug_data.get('message')}")
        else:
            print(f"❌ Debug request failed: {debug_response.status_code}")
        
        print()
        print("🔗 Next Steps:")
        print(f"1. Go to: {auth_data.get('verification_uri')}")
        print(f"2. Enter code: {auth_data.get('user_code')}")
        print(f"3. You have {auth_data.get('expires_in', 0)/60:.1f} minutes to complete")
        print()
        print("💡 Test endpoints:")
        print(f"📊 Debug status: GET {RAILWAY_URL}/api/onedrive/debug/flow-status")
        print(f"🔄 Check auth: GET {RAILWAY_URL}/api/onedrive/auth/check")
        print(f"⏰ Extend timeout: POST {RAILWAY_URL}/api/onedrive/extend-timeout")
        
        # Optional: Monitor the flow
        monitor_choice = input("\n❓ Do you want to monitor the flow status? (y/n): ").lower().strip()
        
        if monitor_choice == 'y':
            monitor_device_flow()
            
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

def monitor_device_flow():
    """Monitor the device flow status in real-time."""
    
    print("\n📊 Monitoring device flow status (press Ctrl+C to stop)...")
    print("-" * 60)
    
    try:
        while True:
            # Check status
            status_response = session.get(f"{RAILWAY_URL}/api/onedrive/auth/check")
            debug_response = session.get(f"{RAILWAY_URL}/api/onedrive/debug/flow-status")
            
            current_time = time.strftime("%H:%M:%S")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                status_msg = status_data.get('status', 'unknown')
                message = status_data.get('message', '')
                
                print(f"[{current_time}] Status: {status_msg} - {message}")
                
                if status_msg in ['success', 'completed', 'error', 'expired']:
                    print(f"🏁 Flow completed with status: {status_msg}")
                    break
            
            if debug_response.status_code == 200:
                debug_data = debug_response.json()
                if debug_data.get('success') and 'time_remaining_minutes' in debug_data:
                    remaining = debug_data['time_remaining_minutes']
                    print(f"[{current_time}] ⏳ Time remaining: {remaining:.1f} minutes")
            
            time.sleep(10)  # Check every 10 seconds
            
    except KeyboardInterrupt:
        print("\n🛑 Monitoring stopped by user")
    except Exception as e:
        print(f"\n❌ Monitoring error: {e}")

def extend_timeout():
    """Test the timeout extension endpoint."""
    
    print("\n🕐 Testing timeout extension...")
    
    try:
        extend_response = session.post(f"{RAILWAY_URL}/api/onedrive/extend-timeout")
        
        if extend_response.status_code == 200:
            extend_data = extend_response.json()
            if extend_data.get('success'):
                print(f"✅ Timeout extended successfully!")
                print(f"⏰ New timeout: {extend_data.get('new_timeout_minutes', 0):.1f} minutes")
                print(f"➕ Added: {extend_data.get('added_minutes', 0):.1f} minutes")
            else:
                print(f"❌ Extension failed: {extend_data.get('error')}")
        else:
            print(f"❌ Extension request failed: {extend_response.status_code}")
            print(f"Response: {extend_response.text}")
    
    except Exception as e:
        print(f"❌ Extension test failed: {e}")

if __name__ == "__main__":
    print("🎯 OneDrive Device Flow Timeout Testing")
    print("=" * 60)
    print()
    print("Available tests:")
    print("1. Full device flow timeout test")
    print("2. Extend timeout test")
    print("3. Monitor active flow")
    print()
    
    choice = input("Enter your choice (1-3): ").strip()
    
    if choice == "1":
        test_device_flow_timeout()
    elif choice == "2":
        extend_timeout()
    elif choice == "3":
        monitor_device_flow()
    else:
        print("❌ Invalid choice")