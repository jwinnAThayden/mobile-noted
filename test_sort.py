#!/usr/bin/env python3
"""
Test script to trigger the sort functionality and check debug output
"""
import tkinter as tk
import time
import threading
from tkinter import messagebox

def auto_sort():
    """Automatically trigger the sort after a short delay"""
    time.sleep(3)  # Wait for app to fully load
    print("TEST: Attempting to trigger sort functionality...")
    
    # Try to find the app instance and call sort
    try:
        # This is a bit hacky but we'll try to access the global app instance
        import sys
        import os
        sys.path.insert(0, os.path.dirname(__file__))
        
        # We'll need to trigger this through the GUI since we can't easily access the app instance
        root = tk._default_root
        if root:
            print("TEST: Found root window, attempting to simulate right-click sort...")
            # Unfortunately, we can't easily simulate a right-click programmatically
            # The user will need to manually right-click and select "Sort All Tabs by Name"
            print("TEST: Please manually right-click on a tab and select 'Sort All Tabs by Name'")
        
    except Exception as e:
        print(f"TEST: Error attempting auto-sort: {e}")

if __name__ == "__main__":
    print("TEST: This script monitors sort functionality")
    print("TEST: The noted.py app should already be running")
    print("TEST: Now manually right-click on any tab and select 'Sort All Tabs by Name'")
    print("TEST: Check the debug output in the noted.py terminal...")