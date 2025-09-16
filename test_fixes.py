#!/usr/bin/env python3
"""
Test script to verify the fixes for closure issues and widget reference errors.
This script creates automated tests for the key functionality.
"""

import tkinter as tk
import sys
import os
import time
import threading

# Add the current directory to Python path to import noted
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_closure_fixes():
    """Test that button closures work correctly in paned view."""
    print("Testing closure fixes...")
    
    # Import after path setup
    from noted import EditableBoxApp
    
    # Create root window
    root = tk.Tk()
    root.withdraw()  # Hide the main window
    
    try:
        # Create app instance
        app = EditableBoxApp(root)
        
        # Force switch to paned view
        app.current_view_mode = "tabbed"  # Start from tabbed to trigger switch
        app.toggle_tabbed_view()  # This should switch to paned
        
        # Wait a moment for UI updates
        root.update()
        
        # Add a few boxes for testing
        app.add_text_box()
        app.add_text_box()
        
        # Wait for UI updates
        root.update()
        
        # Verify we have text boxes
        if len(app.text_boxes) >= 2:
            print(f"✓ Created {len(app.text_boxes)} text boxes successfully")
            
            # Add some content to test with
            for i, box_data in enumerate(app.text_boxes):
                text_widget = box_data.get("text_box")
                if text_widget:
                    text_widget.insert("1.0", f"Test content for box {i+1}")
            
            # Test arrangement cycling (this was causing widget reference errors)
            print("Testing arrangement cycling...")
            try:
                app.cycle_box_arrangement()
                root.update()
                print("✓ Arrangement cycling works without errors")
                
                # Test again to cycle back
                app.cycle_box_arrangement()
                root.update()
                print("✓ Second arrangement cycle works without errors")
                
            except Exception as e:
                print(f"✗ Arrangement cycling failed: {e}")
                return False
                
        else:
            print("✗ Failed to create text boxes")
            return False
            
        print("✓ All closure and widget reference tests passed!")
        return True
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        return False
    finally:
        # Clean up
        try:
            root.quit()
            root.destroy()
        except:
            pass

def test_view_switching():
    """Test that view switching preserves content correctly."""
    print("\nTesting view switching...")
    
    from noted import EditableBoxApp
    
    root = tk.Tk()
    root.withdraw()
    
    try:
        app = EditableBoxApp(root)
        
        # Start in tabbed mode, add content
        test_content = "This is test content that should be preserved"
        
        # Get the current tab's text widget
        if hasattr(app, 'notebook') and app.notebook:
            current_tab = app.notebook.tabs()[0] if app.notebook.tabs() else None
            if current_tab:
                tab_frame = app.notebook.nametowidget(current_tab)
                for child in tab_frame.winfo_children():
                    if isinstance(child, tk.Text):
                        child.insert("1.0", test_content)
                        break
        
        root.update()
        
        # Switch to paned view
        app.toggle_tabbed_view()
        root.update()
        
        # Check if content was preserved
        content_preserved = False
        if app.text_boxes:
            for box_data in app.text_boxes:
                text_widget = box_data.get("text_box")
                if text_widget:
                    content = text_widget.get("1.0", tk.END).strip()
                    if test_content in content:
                        content_preserved = True
                        break
        
        if content_preserved:
            print("✓ Content preserved during view switching")
        else:
            print("✗ Content lost during view switching")
            return False
            
        # Switch back to tabbed
        app.toggle_tabbed_view()
        root.update()
        
        print("✓ View switching test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ View switching test failed: {e}")
        return False
    finally:
        try:
            root.quit()
            root.destroy()
        except:
            pass

if __name__ == "__main__":
    print("Running automated tests for noted.py fixes...")
    print("=" * 50)
    
    # Run tests
    test1_passed = test_closure_fixes()
    test2_passed = test_view_switching()
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print(f"Closure fixes test: {'PASSED' if test1_passed else 'FAILED'}")
    print(f"View switching test: {'PASSED' if test2_passed else 'FAILED'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 All tests PASSED! The fixes are working correctly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests FAILED. Please check the implementation.")
        sys.exit(1)