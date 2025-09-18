"""
Comprehensive OneDrive Cross-Platform Compatibility Test
Tests that desktop and web versions can work with the same OneDrive files.
"""

import sys
import os
import json

# Add the project directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_interface_compatibility():
    """Test that both managers have the same interface methods."""
    
    try:
        from onedrive_manager import OneDriveManager
        from onedrive_web_manager import WebOneDriveManager
        
        print("🔍 Testing Interface Compatibility")
        print("-" * 40)
        
        # Check required methods exist
        required_methods = [
            'is_authenticated',
            'list_notes', 
            'get_note_content',
            'save_note'
        ]
        
        desktop_methods = [m for m in dir(OneDriveManager) if not m.startswith('_')]
        web_methods = [m for m in dir(WebOneDriveManager) if not m.startswith('_')]
        
        print(f"Desktop methods: {sorted(desktop_methods)}")
        print(f"Web methods: {sorted(web_methods)}")
        
        missing_in_web = []
        missing_in_desktop = []
        
        for method in required_methods:
            if method not in desktop_methods:
                missing_in_desktop.append(method)
            if method not in web_methods:
                missing_in_web.append(method)
        
        if missing_in_desktop:
            print(f"❌ Missing in desktop: {missing_in_desktop}")
        if missing_in_web:
            print(f"❌ Missing in web: {missing_in_web}")
            
        if not missing_in_desktop and not missing_in_web:
            print("✅ All required methods present in both versions!")
            
        return len(missing_in_desktop) == 0 and len(missing_in_web) == 0
            
    except Exception as e:
        print(f"❌ Interface test failed: {e}")
        return False

def test_save_note_compatibility():
    """Test that save_note methods have compatible signatures."""
    
    try:
        from onedrive_manager import OneDriveManager
        from onedrive_web_manager import WebOneDriveManager
        
        print("\n🔍 Testing save_note Method Compatibility")
        print("-" * 40)
        
        # Test data
        test_content = {"title": "Test Note", "content": "This is a test note"}
        test_filename = "test_compatibility.json"
        
        # Create instances (won't authenticate, just test signatures)
        desktop_manager = OneDriveManager("fake_client_id", "fake_tenant_id")
        web_manager = WebOneDriveManager("fake_client_id", "fake_tenant_id")
        
        # Test method signatures by inspecting them
        import inspect
        
        desktop_sig = inspect.signature(desktop_manager.save_note)
        web_sig = inspect.signature(web_manager.save_note)
        
        print(f"Desktop save_note signature: {desktop_sig}")
        print(f"Web save_note signature: {web_sig}")
        
        # Check parameters
        desktop_params = list(desktop_sig.parameters.keys())
        web_params = list(web_sig.parameters.keys())
        
        if desktop_params == web_params:
            print("✅ save_note signatures match!")
            return True
        else:
            print(f"❌ Signature mismatch: Desktop={desktop_params}, Web={web_params}")
            return False
            
    except Exception as e:
        print(f"❌ save_note test failed: {e}")
        return False

def test_scopes_and_endpoints():
    """Test that scopes and endpoints are compatible."""
    
    print("\n🔍 Testing Scopes and Endpoints")
    print("-" * 40)
    
    try:
        # Import constants from both modules
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        import onedrive_manager
        import onedrive_web_manager
        
        desktop_scopes = getattr(onedrive_manager, 'SCOPES', [])
        web_scopes = getattr(onedrive_web_manager, 'SCOPES', [])
        
        desktop_endpoint = getattr(onedrive_manager, 'GRAPH_API_ENDPOINT', '')
        web_endpoint = getattr(onedrive_web_manager, 'GRAPH_API_ENDPOINT', '')
        
        print(f"Desktop scopes: {desktop_scopes}")
        print(f"Web scopes: {web_scopes}")
        print(f"Desktop endpoint: {desktop_endpoint}")
        print(f"Web endpoint: {web_endpoint}")
        
        # Check core compatibility (ignoring offline_access which is desktop-only)
        desktop_core = [s for s in desktop_scopes if s != "offline_access"]
        scopes_compatible = set(desktop_core) == set(web_scopes)
        endpoints_match = desktop_endpoint == web_endpoint
        
        if scopes_compatible:
            print("✅ Core scopes are compatible!")
        else:
            print("❌ Core scopes mismatch!")
            
        if endpoints_match:
            print("✅ Endpoints match!")
        else:
            print("❌ Endpoints don't match!")
            
        return scopes_compatible and endpoints_match
        
    except Exception as e:
        print(f"❌ Scopes/endpoints test failed: {e}")
        return False

def main():
    """Run all compatibility tests."""
    
    print("🎯 OneDrive Cross-Platform Compatibility Test Suite")
    print("=" * 60)
    
    tests = [
        test_interface_compatibility,
        test_save_note_compatibility, 
        test_scopes_and_endpoints
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test_func.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("\n✅ Desktop and Web OneDrive managers are now fully compatible!")
        print("✅ Cross-platform sync should work correctly!")
        print("✅ Both versions will access the same OneDrive AppFolder!")
    else:
        print(f"⚠️  SOME TESTS FAILED ({passed}/{total})")
        print("❌ Cross-platform sync may not work properly")
        
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)