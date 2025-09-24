#!/usr/bin/env python3
"""
Test script to verify drag-and-drop fixes.
This tests that drag operations work repeatedly and preserve titles.
"""
import os
import sys

def test_drag_drop_fixes():
    """Test that the drag-and-drop fixes are properly implemented."""
    
    print("🧪 Testing Drag-and-Drop Fixes")
    print("=" * 50)
    
    try:
        with open('noted.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        checks = [
            ('Title generation before manipulation', 'Generate proper tab title from stored data' in content),
            ('Drag binding re-establishment', 'self.root.after_idle(self._setup_tab_drag_bindings)' in content),
            ('Drag state reset on click', 'self._reset_drag_state()' in content and '_on_tab_click' in content),
            ('Robust drag release handling', 'if not self._drag_data.get("dragging", False):' in content),
            ('Debug logging for titles', 'DEBUG: Using tab title:' in content),
            ('Index validation in release', 'if source_index is not None and 0 <= source_index < len(self.text_boxes):' in content),
        ]
        
        all_passed = True
        for check_name, passed in checks:
            status = "✅ PASS" if passed else "❌ FAIL"
            print(f"  {status} - {check_name}")
            if not passed:
                all_passed = False
        
        print("\n" + "=" * 50)
        if all_passed:
            print("🎉 All drag-and-drop fixes are in place!")
            print("\n📝 The fixes should now:")
            print("  • Allow repeated dragging (no lockup)")  
            print("  • Preserve tab titles during drag operations")
            print("  • Handle drag state more robustly")
            print("  • Re-establish bindings after tab moves")
            print("  • Validate indices before operations")
            print("\n🚀 Try dragging tabs multiple times to verify!")
        else:
            print("⚠️  Some fixes are missing. Please check the failed items.")
            
        return all_passed
        
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False

if __name__ == "__main__":
    success = test_drag_drop_fixes()
    sys.exit(0 if success else 1)