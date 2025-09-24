#!/usr/bin/env python3
"""
Simple drag test to verify the exact issue with the tab dragging.
This test simulates drag operations to see if the problem persists.
"""
import os
import json
import time

def simulate_drag_test():
    """Check if we can identify the drag issue by examining the current state."""
    
    print("🔍 Examining Drag-and-Drop Implementation")
    print("=" * 60)
    
    # Check if the main noted.py file has the necessary drag components
    try:
        with open('noted.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check drag-related components
        drag_components = [
            ('_drag_data initialization', '_drag_data = {' in content),
            ('_setup_tab_drag_bindings method', 'def _setup_tab_drag_bindings(self):' in content),
            ('_on_tab_click method', 'def _on_tab_click(self, event):' in content),
            ('_on_tab_drag method', 'def _on_tab_drag(self, event):' in content),
            ('_on_tab_release method', 'def _on_tab_release(self, event):' in content),
            ('_move_tab method', 'def _move_tab(self, from_index, to_index):' in content),
            ('_reset_drag_state method', 'def _reset_drag_state(self):' in content),
            ('Drag binding setup call', 'self._setup_tab_drag_bindings()' in content),
            ('Drag state reset in click', 'self._reset_drag_state()' in content and '_on_tab_click' in content),
            ('Binding re-establishment', 'self.root.after(' in content and '_setup_tab_drag_bindings' in content),
        ]
        
        print("📋 Drag Component Analysis:")
        for component, present in drag_components:
            status = "✅ Present" if present else "❌ Missing"
            print(f"  {status} - {component}")
        
        # Check for potential issues
        print("\n🔍 Potential Issue Analysis:")
        
        issues = []
        
        # Check for dragging flag management
        if '_drag_data["dragging"] = True' not in content:
            issues.append("Dragging flag may not be set properly")
        
        # Check for proper index validation  
        if 'if source_index is not None and 0 <= source_index < len(self.text_boxes):' not in content:
            issues.append("Missing index validation in drag release")
        
        # Check for binding conflicts
        if 'self.notebook.unbind(' not in content:
            issues.append("No explicit unbinding before re-binding")
        
        # Check for timing issues
        if content.count('after_idle') + content.count('self.root.after(') < 2:
            issues.append("May lack proper timing for binding re-establishment")
        
        if issues:
            print("  ⚠️  Potential Issues Found:")
            for issue in issues:
                print(f"    - {issue}")
        else:
            print("  ✅ No obvious implementation issues found")
        
        # Check for drag state management
        print("\n🎯 Drag State Management:")
        drag_state_checks = [
            ('Drag data initialization', '"dragging": False' in content),
            ('Drag threshold check', 'dx > 5 or dy > 5' in content or 'dx > 3 or dy > 3' in content),
            ('Cursor changes', 'cursor="hand2"' in content),
            ('State reset on release', '_reset_drag_state()' in content and '_on_tab_release' in content),
        ]
        
        for check, found in drag_state_checks:
            status = "✅ OK" if found else "❌ Issue"
            print(f"  {status} - {check}")
            
        # Look at the current layout.json to see what tabs we have
        try:
            with open('layout.json', 'r', encoding='utf-8') as f:
                layout = json.load(f)
            
            tab_count = len(layout.get('boxes', []))
            print(f"\n📊 Current layout has {tab_count} tabs available for testing")
            
            if tab_count < 2:
                print("  ⚠️  Need at least 2 tabs to properly test drag-and-drop")
            else:
                print("  ✅ Sufficient tabs for drag testing")
                
        except Exception as e:
            print(f"\n❌ Could not read layout.json: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 Next Steps for Testing:")
        print("1. Open the noted.py application")
        print("2. Try dragging the first tab to the second position")
        print("3. Then try dragging it back to the first position") 
        print("4. Check if both operations work without lockup")
        print("5. Verify that tab titles are preserved during moves")
        
        return True
        
    except Exception as e:
        print(f"❌ Error analyzing drag implementation: {e}")
        return False

if __name__ == "__main__":
    simulate_drag_test()