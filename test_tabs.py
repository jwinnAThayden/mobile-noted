#!/usr/bin/env python3
"""Test script to verify horizontal tab display in Noted app."""

import tkinter as tk
from tkinter import ttk
import noted

def test_horizontal_tabs():
    """Test horizontal tab display."""
    print("Testing horizontal tabs in Noted app...")
    
    # Create the app
    root = tk.Tk()
    root.title("Noted - Tab Test")
    root.geometry("800x600")  # Set a specific size for testing
    
    app = noted.EditableBoxApp(root)
    
    # Add multiple text boxes to test with multiple tabs
    print("Adding multiple text boxes...")
    app.add_text_box()
    app.add_text_box() 
    app.add_text_box()
    app.add_text_box()
    
    # Ensure we're in tabbed view  
    if not app.notebook:
        print("Switching to tabbed view...")
        app.toggle_tabbed_view()
    
    # Add some content to make tabs more distinguishable
    for i, text_box_data in enumerate(app.text_boxes):
        text_widget = text_box_data.get("text_box")
        if text_widget:
            text_widget.insert("1.0", f"This is content for Tab {i+1}\nWith some sample text to make the tab meaningful.")
    
    print("Tabs created. Check if they are displayed horizontally across the top.")
    print("Window size: 800x600")
    print(f"Number of tabs: {len(app.text_boxes)}")
    
    # Check notebook configuration
    if app.notebook:
        print(f"Notebook exists: {app.notebook}")
        print(f"Number of notebook tabs: {len(app.notebook.tabs())}")
        
        # Force update to ensure all styles are applied
        app.notebook.update_idletasks()
        
    root.mainloop()

if __name__ == "__main__":
    test_horizontal_tabs()