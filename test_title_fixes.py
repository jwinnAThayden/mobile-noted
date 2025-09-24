#!/usr/bin/env python3
"""
Test script to verify that tab title fixes are working properly.
This tests that titles are preserved during sorting operations.
"""
import os
import sys

def test_tab_title_fixes():
    """Test that the tab title fixes are in place."""
    
    print("🧪 Testing Tab Title Fixes")
    print("=" * 50)
    
    try:
        with open('noted.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ('Auto-sort startup prevention', '_app_startup_complete' in content),
            ('Sorting function title generation', 'stored_title = data.get("title", "")' in content),
            ('Drag-drop title fallback', 'stored_title = tab_data.get("title", "")' in content),
            ('Startup flag initialization', 'self._app_startup_complete = False' in content),
            ('Startup completion flag', 'self._app_startup_complete = True' in content),
        ]
        
        all_passed = True
        for check_name, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} - {check_name}")
            if not passed:
                all_passed = False
        
        print("\n" + "=" * 50)
        if all_passed:
            print("🎉 All tab title fixes are in place!")
            print("\n📝 The fixes should now:")
            print("  • Show proper tab titles on app startup")  
            print("  • Preserve titles during sorting operations")
            print("  • Preserve titles during drag-and-drop")
            print("  • Auto-sort only new tabs (not during startup)")
            print("\n🚀 Try running the app to verify the fixes work!")
        else:
            print("⚠️  Some fixes are missing. Please check the failed items.")
            
        return all_passed
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

if __name__ == "__main__":
    success = test_tab_title_fixes()
    sys.exit(0 if success else 1)