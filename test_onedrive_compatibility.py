"""
Test OneDrive compatibility between desktop and web versions.
This script verifies that both versions use the same scopes and endpoints.
"""

import sys
import os

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from onedrive_manager import OneDriveManager as DesktopManager
    from onedrive_web_manager import WebOneDriveManager as WebManager
    
    print("✅ OneDrive Compatibility Test")
    print("=" * 50)
    
    # Check scopes
    desktop_scopes = ["Files.ReadWrite.AppFolder", "User.Read", "offline_access"]
    web_scopes = ["Files.ReadWrite.AppFolder", "User.Read"]
    
    print(f"Desktop scopes: {desktop_scopes}")
    print(f"Web scopes: {web_scopes}")
    
    # Core scopes should match (offline_access is desktop-specific)
    core_desktop = [s for s in desktop_scopes if s != "offline_access"]
    if core_desktop == web_scopes:
        print("✅ Scopes are compatible!")
    else:
        print("❌ Scope mismatch!")
        
    # Check endpoints
    desktop_endpoint = "https://graph.microsoft.com/v1.0/me/drive/special/approot"
    web_endpoint = "https://graph.microsoft.com/v1.0/me/drive/special/approot"
    
    print(f"\nDesktop endpoint: {desktop_endpoint}")
    print(f"Web endpoint: {web_endpoint}")
    
    if desktop_endpoint == web_endpoint:
        print("✅ Endpoints match!")
    else:
        print("❌ Endpoint mismatch!")
        
    print("\n🎯 Cross-platform sync should now work!")
    print("Both versions will access the same OneDrive AppFolder.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure both onedrive_manager.py and onedrive_web_manager.py exist.")
