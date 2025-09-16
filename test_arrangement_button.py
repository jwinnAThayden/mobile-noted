#!/usr/bin/env python3
"""
Simple test to manually trigger the arrangement method and see debug output.
"""

import sys
import os

# Add the noted directory to the path so we can import the module
sys.path.insert(0, os.path.dirname(__file__))

# Import the noted module (but don't run the GUI)
import tkinter as tk

# Create a minimal test of the arrangement logic
def test_arrangement_methods():
    print("Testing arrangement methods...")
    
    # Create a simple root window for testing
    root = tk.Tk()
    root.withdraw()  # Hide the window
    
    # Create a minimal mock of the EditableBoxApp
    class MockApp:
        def __init__(self):
            self.current_arrangement = "horizontal"
            self.text_boxes = [
                {"outer_frame": None},
                {"outer_frame": None},
                {"outer_frame": None}
            ]
            
        def cycle_box_arrangement(self):
            """Test version of cycle_box_arrangement"""
            print("DEBUG: Arrange Boxes button clicked!")
            print(f"DEBUG: Current arrangement before toggle: {self.current_arrangement}")
            print(f"DEBUG: Number of text boxes: {len(self.text_boxes)}")
            
            # Simple toggle between horizontal and vertical
            if self.current_arrangement == "horizontal":
                self.current_arrangement = "vertical"
            else:
                self.current_arrangement = "horizontal"
            
            print(f"DEBUG: Arrangement changed to {self.current_arrangement}")
            print(f"DEBUG: Would apply {self.current_arrangement} arrangement to {len(self.text_boxes)} boxes")
    
    # Test the logic
    app = MockApp()
    
    print("\nTesting 5 button clicks:")
    for i in range(1, 6):
        print(f"\n--- Button Click {i} ---")
        app.cycle_box_arrangement()
    
    root.destroy()

if __name__ == "__main__":
    test_arrangement_methods()
