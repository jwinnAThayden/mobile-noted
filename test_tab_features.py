#!/usr/bin/env python3
"""
Test file to verify tab sorting and drag-and-drop functionality.
Run this to create multiple test tabs and try the new features.
"""
import os
import sys
import tempfile
import shutil

def create_test_files():
    """Create some test files with different names to test sorting."""
    try:
        # Create temporary directory
        test_dir = tempfile.mkdtemp(prefix="noted_test_")
        print(f"Creating test files in: {test_dir}")
        
        # Create test files with different names
        test_files = [
            ("zebra.txt", "This is the zebra file - should sort last"),
            ("apple.txt", "This is the apple file - should sort first"),  
            ("banana.txt", "This is the banana file - should sort second"),
            ("cherry.txt", "This is the cherry file - should sort third"),
            ("dog.txt", "This is the dog file - should sort fourth")
        ]
        
        created_files = []
        for filename, content in test_files:
            filepath = os.path.join(test_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            created_files.append(filepath)
            print(f"Created: {filepath}")
        
        print(f"\nTest files created! You can now:")
        print(f"1. Run 'python noted.py' to start the app")
        print(f"2. Open these files to create tabs:")
        for filepath in created_files:
            print(f"   - {filepath}")
        print(f"3. Right-click on any tab and select 'Sort All Tabs by Name'")
        print(f"4. Try dragging tabs to rearrange them manually")
        print(f"5. Tabs should auto-sort: apple, banana, cherry, dog, zebra")
        print(f"\nTest directory: {test_dir}")
        print(f"Remember to clean up when done!")
        
        return test_dir, created_files
        
    except Exception as e:
        print(f"Error creating test files: {e}")
        return None, []

def cleanup_test_files(test_dir):
    """Clean up test files."""
    try:
        if test_dir and os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"Cleaned up test directory: {test_dir}")
    except Exception as e:
        print(f"Error cleaning up: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "cleanup":
        # Look for test directories to clean up
        temp_parent = tempfile.gettempdir()
        test_dirs = [d for d in os.listdir(temp_parent) if d.startswith("noted_test_")]
        for test_dir in test_dirs:
            full_path = os.path.join(temp_parent, test_dir)
            cleanup_test_files(full_path)
        print("Cleanup complete!")
    else:
        test_dir, files = create_test_files()
        if test_dir:
            print(f"\nTo clean up later, run: python {__file__} cleanup")