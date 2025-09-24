#!/usr/bin/env python3
"""
Verification test for tab sorting and drag-drop fixes.
This checks that the key functions exist and are properly integrated.
"""
import os
import sys

# Add the current directory to the path to import noted
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_functions_exist():
    """Test that all necessary functions exist in the noted module."""
    try:
        # Import the EditableBoxApp class
        from noted import EditableBoxApp
        
        # Check that all the key methods exist
        methods_to_check = [
            'sort_tabs_by_name',
            '_sort_tab_data_by_name', 
            '_setup_tab_drag_bindings',
            '_move_tab',
            '_on_tab_click',
            '_on_tab_drag',
            '_on_tab_release',
            'add_text_box'
        ]
        
        print("🔍 Checking for required methods...")
        missing_methods = []
        
        for method_name in methods_to_check:
            if hasattr(EditableBoxApp, method_name):
                print(f"  ✅ {method_name} - Found")
            else:
                print(f"  ❌ {method_name} - MISSING")
                missing_methods.append(method_name)
        
        if missing_methods:
            print(f"\n❌ Missing methods: {missing_methods}")
            return False
        else:
            print("\n✅ All required methods found!")
            return True
            
    except Exception as e:
        print(f"❌ Error checking functions: {e}")
        return False

def test_auto_sort_integration():
    """Test that auto-sort is integrated into add_text_box."""
    try:
        with open('noted.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for auto-sort integration in add_text_box
        if 'self.root.after_idle(self.sort_tabs_by_name)' in content:
            print("✅ Auto-sort integration found in add_text_box")
            return True
        else:
            print("❌ Auto-sort integration NOT found in add_text_box")
            return False
            
    except Exception as e:
        print(f"❌ Error checking auto-sort integration: {e}")
        return False

def test_drag_drop_title_fix():
    """Test that drag-drop title preservation is fixed."""
    try:
        with open('noted.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for improved title fallback in _move_tab
        if 'stored_title = tab_data.get("title", "")' in content:
            print("✅ Drag-drop title preservation fix found")
            return True
        else:
            print("❌ Drag-drop title preservation fix NOT found")
            return False
            
    except Exception as e:
        print(f"❌ Error checking drag-drop fix: {e}")
        return False

def main():
    """Run all verification tests."""
    print("🧪 Testing Tab Sorting & Drag-Drop Fixes")
    print("=" * 50)
    
    tests = [
        ("Function Existence", test_functions_exist),
        ("Auto-Sort Integration", test_auto_sort_integration), 
        ("Drag-Drop Title Fix", test_drag_drop_title_fix)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        print("-" * 30)
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {test_name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed! The fixes should be working.")
        print("\n📝 To test manually:")
        print("  1. Run: python noted.py")
        print("  2. Open multiple test files (they should auto-sort)")
        print("  3. Try dragging tabs (titles should be preserved)")
        print("  4. Right-click → 'Sort All Tabs by Name' should work")
    else:
        print("\n⚠️  Some tests failed. Please check the issues above.")

if __name__ == "__main__":
    main()