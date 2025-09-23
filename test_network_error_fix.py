"""
Test Network Error Fix for Notes Loading

This test verifies that the network error when loading notes has been resolved.

Issue:
- Frontend was trying to fetch CSRF tokens from /login endpoint
- When authentication is disabled, /login redirects to /, causing fetch errors
- This prevented notes from loading with "NetworkError when attempting to fetch resource"

Fix Applied:
- Enhanced getCsrfToken() function to handle disabled authentication gracefully
- Added multiple fallback methods for CSRF token retrieval
- Added /api/csrf-token endpoint that returns appropriate response when CSRF is disabled
- Frontend now handles missing CSRF tokens without throwing network errors

Expected Behavior:
1. When authentication/CSRF is disabled, getCsrfToken() returns null without errors
2. authenticatedFetch() works with null CSRF token (doesn't include X-CSRFToken header)
3. Notes load successfully without network errors
4. App functions normally in no-auth mode
"""

import requests
import time

def test_notes_loading():
    """Test that notes can be loaded without network errors"""
    try:
        response = requests.get('https://mobile-noted-production.up.railway.app/api/notes', timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Notes API working correctly")
                return True
            else:
                print(f"❌ Notes API returned error: {data.get('error', 'Unknown error')}")
                return False
        else:
            print(f"❌ Notes API returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Network error when loading notes: {e}")
        return False

def test_csrf_endpoint():
    """Test that CSRF endpoint handles disabled auth correctly"""
    try:
        response = requests.get('https://mobile-noted-production.up.railway.app/api/csrf-token', timeout=10)
        
        if response.status_code == 404:
            data = response.json()
            if data.get('error') == 'CSRF protection disabled':
                print("✅ CSRF endpoint correctly reports disabled protection")
                return True
            else:
                print(f"❌ Unexpected CSRF endpoint response: {data}")
                return False
        elif response.status_code == 200:
            data = response.json()
            if 'csrf_token' in data:
                print("✅ CSRF endpoint returned token (auth enabled)")
                return True
            else:
                print(f"❌ CSRF endpoint missing token: {data}")
                return False
        else:
            print(f"❌ CSRF endpoint returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing CSRF endpoint: {e}")
        return False

def test_main_page_loads():
    """Test that the main page loads without errors"""
    try:
        response = requests.get('https://mobile-noted-production.up.railway.app/', timeout=10)
        
        if response.status_code == 200:
            # Check that the page contains the JavaScript functions we fixed
            html = response.text
            checks = [
                'function getCsrfToken' in html,
                'function authenticatedFetch' in html,
                'function loadNotes' in html,
                '/api/csrf-token' in html  # Our new endpoint reference
            ]
            
            if all(checks):
                print("✅ Main page loads with updated JavaScript functions")
                return True
            else:
                print("❌ Main page missing expected JavaScript functions")
                return False
        else:
            print(f"❌ Main page returned status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error loading main page: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Network Error Fix for Notes Loading")
    print("=" * 50)
    
    print("⏳ Waiting for Railway deployment...")
    time.sleep(15)
    
    test1_result = test_notes_loading()
    test2_result = test_csrf_endpoint()  
    test3_result = test_main_page_loads()
    
    if test1_result and test2_result and test3_result:
        print("\n🎉 Network error fix verification PASSED!")
        print("✅ Notes should load without NetworkError")
        print("✅ CSRF token handling improved for disabled auth")
        print("✅ App should work normally in no-auth mode")
    else:
        print("\n❌ Network error fix verification FAILED")
        print("🔧 Some issues may remain - check individual test results")