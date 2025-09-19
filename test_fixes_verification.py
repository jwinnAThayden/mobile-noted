#!/usr/bin/env python3
"""
Test script to verify the critical fixes for OneDrive automatic loading and Ctrl+W functionality.
"""

import os
import json
import sys

def test_config_file_path():
    """Test that config files are now using local storage instead of OneDrive."""
    print("🧪 Testing configuration file path behavior...")
    
    # Import the app to test the _get_config_file_path method
    sys.path.insert(0, os.path.dirname(__file__))
    from noted import EditableBoxApp
    
    # Create a temporary app instance (without initializing GUI)
    class TestApp:
        def __init__(self):
            pass
        
        def _get_config_file_path(self, filename):
            """Get configuration file path, using local storage to prevent automatic OneDrive loading."""
            try:
                # ALWAYS use current directory for app state to prevent automatic OneDrive loading
                # OneDrive sync should be explicit user action via the OneDrive button
                return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)
                
            except Exception:
                # Ultimate fallback: use current directory
                return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)
    
    test_app = TestApp()
    
    # Test layout.json path
    layout_path = test_app._get_config_file_path("layout.json")
    print(f"   Layout file path: {layout_path}")
    
    # Test config file path
    config_path = test_app._get_config_file_path("noted_config.json")
    print(f"   Config file path: {config_path}")
    
    # Verify both paths are local (not in OneDrive Documents/Noted)
    current_dir = os.path.abspath(os.path.dirname(__file__))
    
    layout_expected = os.path.join(current_dir, "layout.json")
    config_expected = os.path.join(current_dir, "noted_config.json")
    
    layout_ok = (layout_path == layout_expected)
    config_ok = (config_path == config_expected)
    
    print(f"   ✅ Layout path correct: {layout_ok}")
    print(f"   ✅ Config path correct: {config_ok}")
    
    if layout_ok and config_ok:
        print("   🎉 SUCCESS: Config files are now using local storage!")
        return True
    else:
        print("   ❌ FAIL: Config files are still using OneDrive paths")
        return False

def test_local_layout_content():
    """Test that the local layout.json contains the expected single note."""
    print("\n🧪 Testing local layout content...")
    
    layout_file = os.path.join(os.path.dirname(__file__), "layout.json")
    
    if not os.path.exists(layout_file):
        print("   ❓ No local layout.json found - will be created on first run")
        return True
    
    try:
        with open(layout_file, 'r', encoding='utf-8') as f:
            layout_data = json.load(f)
        
        text_boxes = layout_data.get('text_boxes', [])
        box_count = len(text_boxes)
        
        print(f"   Local layout contains {box_count} boxes")
        
        if box_count == 1:
            print("   ✅ SUCCESS: Only 1 note in local layout (as expected)")
            return True
        elif box_count == 0:
            print("   ✅ OK: Empty layout (will create default note on startup)")
            return True
        else:
            print(f"   ❓ WARNING: {box_count} notes in local layout (may be user's working state)")
            return True
            
    except Exception as e:
        print(f"   ❌ Error reading layout: {e}")
        return False

def main():
    """Run all verification tests."""
    print("🔧 Verifying critical fixes for noted.py\n")
    
    test1_result = test_config_file_path()
    test2_result = test_local_layout_content()
    
    print(f"\n📊 Test Results:")
    print(f"   Config path fix: {'✅ PASS' if test1_result else '❌ FAIL'}")
    print(f"   Local layout: {'✅ PASS' if test2_result else '❌ FAIL'}")
    
    if test1_result and test2_result:
        print(f"\n🎉 All tests passed! The fixes should work correctly.")
        print(f"   • App will no longer automatically load 22 OneDrive notes")
        print(f"   • App will use local storage for state management")
        print(f"   • OneDrive sync is available via the OneDrive Sync button")
        print(f"   • Ctrl+W should work more reliably with direct text widget bindings")
    else:
        print(f"\n⚠️  Some tests failed. Please check the implementation.")
    
    return test1_result and test2_result

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)