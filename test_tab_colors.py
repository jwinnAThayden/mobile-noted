#!/usr/bin/env python3
"""
Test script to demonstrate tab coloring with multiple tabs.
"""

import tkinter as tk
from tkinter import ttk
import sys
import os

# Add the current directory to Python path to import noted
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_multiple_tabs():
    """Test tab coloring with multiple tabs."""
    print("Testing multiple tab colors...")
    
    # Import after path setup
    from noted import EditableBoxApp
    
    # Create root window
    root = tk.Tk()
    root.title("Tab Color Test")
    
    try:
        # Create app instance
        app = EditableBoxApp(root)
        
        # Make sure we're in tabbed mode
        if app.current_view_mode != "tabbed":
            app.toggle_tabbed_view()
        
        # Wait for UI updates
        root.update()
        
        # Switch to paned view to add multiple boxes, then back to tabbed to see colors
        app.toggle_tabbed_view()  # Switch to paned
        root.update()
        
        # Add some test boxes with content
        for i in range(4):
            app.add_text_box(content=f"This is test content for tab {i+1}\nEach tab should have a different color theme!")
            root.update()
        
        # Switch back to tabbed to see the colorful tabs
        app.toggle_tabbed_view()  # Switch to tabbed
        root.update()
        
        print("✓ Multiple tabs created with different colors!")
        print("✓ You should see:")
        print("  - Tab titles with [1] ■■■, [2] ■■■, etc.")
        print("  - Different colored header bars inside each tab")
        print("  - Different colored borders around the text areas")
        
        # Keep the window open for viewing
        print("\nPress Ctrl+C in the terminal to close the test window.")
        root.mainloop()
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            root.quit()
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    print("Tab Color Test for Noted Application")
    print("=" * 40)
    test_multiple_tabs()