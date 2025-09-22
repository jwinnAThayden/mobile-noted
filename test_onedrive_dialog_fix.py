"""
Test OneDrive Dialog Progress Display Fix

This test verifies that the OneDrive authentication dialog properly displays
device flow information (verification URL, user code, and progress bar).

Issue Fixed:
- JavaScript was trying to update elements with IDs: verificationUrl, deviceCode
- HTML elements had different IDs: verificationUri, userCode  
- This caused the device flow information to not display properly

Fix Applied:
- Changed HTML IDs to match JavaScript expectations:
  - verificationUri → verificationUrl
  - userCode → deviceCode
- Added missing progressFill element to device flow display
- Fixed duplicate progressFill ID by renaming auth progress element to authProgressFill

Expected Behavior:
1. User clicks "Connect OneDrive" 
2. Dialog shows "Device Authentication" section with:
   - Verification URL to visit
   - User code to enter
   - Progress bar showing time remaining
   - Check Status and Cancel buttons
3. User can complete authentication flow using displayed information
"""

import requests
import time

def test_onedrive_dialog_elements():
    """Test that OneDrive dialog contains correct elements"""
    try:
        # Get the web page
        response = requests.get('https://mobile-noted-production.up.railway.app/', timeout=10)
        html_content = response.text
        
        # Check for corrected element IDs
        required_elements = [
            'id="verificationUrl"',  # Fixed from verificationUri
            'id="deviceCode"',       # Fixed from userCode  
            'id="progressFill"',     # Progress bar element
            'id="deviceFlowDisplay"', # Container element
            'id="authProgressFill"'  # Renamed duplicate to avoid conflicts
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in html_content:
                missing_elements.append(element)
        
        if missing_elements:
            print(f"❌ Missing elements: {missing_elements}")
            return False
        else:
            print("✅ All required OneDrive dialog elements found")
            return True
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_javascript_function_compatibility():
    """Test that JavaScript displayDeviceFlow function will work with HTML"""
    try:
        response = requests.get('https://mobile-noted-production.up.railway.app/', timeout=10)
        html_content = response.text
        
        # Check that displayDeviceFlow function exists and references correct IDs
        checks = [
            'function displayDeviceFlow' in html_content,
            'getElementById(\'verificationUrl\')' in html_content,
            'getElementById(\'deviceCode\')' in html_content,  
            'getElementById(\'progressFill\')' in html_content
        ]
        
        if all(checks):
            print("✅ JavaScript displayDeviceFlow function properly references HTML elements")
            return True
        else:
            print("❌ JavaScript function compatibility issues found")
            return False
            
    except Exception as e:
        print(f"❌ JavaScript compatibility test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing OneDrive Dialog Progress Display Fix")
    print("=" * 50)
    
    # Wait a moment for Railway deployment
    print("⏳ Waiting for Railway deployment...")
    time.sleep(30)
    
    test1_result = test_onedrive_dialog_elements()
    test2_result = test_javascript_function_compatibility()
    
    if test1_result and test2_result:
        print("\n🎉 OneDrive dialog fix verification PASSED!")
        print("✅ Users should now see proper device flow authentication UI")
    else:
        print("\n❌ OneDrive dialog fix verification FAILED")
        print("🔧 Additional debugging may be needed")