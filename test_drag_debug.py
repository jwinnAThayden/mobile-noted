#!/usr/bin/env python3
"""
Debug test for drag-and-drop issues.
This will help identify exactly what's happening with the drag functionality.
"""
import tkinter as tk
from tkinter import ttk
import time

class DragTestApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Drag Debug Test")
        self.root.geometry("800x400")
        
        # Drag state tracking
        self._drag_data = {
            "dragging": False,
            "start_tab": None,
            "start_x": 0,
            "start_y": 0
        }
        
        # Create notebook with some test tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add test tabs
        for i in range(5):
            frame = ttk.Frame(self.notebook)
            label = ttk.Label(frame, text=f"Content for Tab {i+1}")
            label.pack(expand=True)
            self.notebook.add(frame, text=f"Tab {i+1}")
        
        # Setup drag bindings
        self.setup_drag_bindings()
        
        # Add status label
        self.status_label = ttk.Label(self.root, text="Ready - try dragging tabs")
        self.status_label.pack(pady=5)
        
        # Add test button to check bindings
        test_button = ttk.Button(self.root, text="Test Bindings", command=self.test_bindings)
        test_button.pack(pady=5)
    
    def setup_drag_bindings(self):
        """Setup drag bindings and report status."""
        try:
            # Clear existing bindings first
            self.notebook.unbind("<Button-1>")
            self.notebook.unbind("<B1-Motion>")
            self.notebook.unbind("<ButtonRelease-1>")
            
            # Set new bindings
            self.notebook.bind("<Button-1>", self.on_tab_click)
            self.notebook.bind("<B1-Motion>", self.on_tab_drag)
            self.notebook.bind("<ButtonRelease-1>", self.on_tab_release)
            
            self.status_label.config(text="Drag bindings setup completed")
            print(f"DEBUG: Drag bindings setup at {time.time()}")
            return True
        except Exception as e:
            self.status_label.config(text=f"Binding setup failed: {e}")
            print(f"ERROR: Binding setup failed: {e}")
            return False
    
    def test_bindings(self):
        """Test if bindings are still active."""
        try:
            # Check if bindings exist
            button_binding = self.notebook.bind("<Button-1>")
            motion_binding = self.notebook.bind("<B1-Motion>")
            release_binding = self.notebook.bind("<ButtonRelease-1>")
            
            active_bindings = []
            if button_binding: active_bindings.append("Button-1")
            if motion_binding: active_bindings.append("B1-Motion") 
            if release_binding: active_bindings.append("ButtonRelease-1")
            
            if active_bindings:
                self.status_label.config(text=f"Active bindings: {', '.join(active_bindings)}")
            else:
                self.status_label.config(text="No bindings found!")
                
        except Exception as e:
            self.status_label.config(text=f"Binding test error: {e}")
    
    def on_tab_click(self, event):
        """Handle tab click."""
        try:
            tab_id = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
            if tab_id != "":
                self._drag_data["dragging"] = False
                self._drag_data["start_tab"] = int(tab_id)
                self._drag_data["start_x"] = event.x
                self._drag_data["start_y"] = event.y
                self.status_label.config(text=f"Clicked tab {tab_id}")
                print(f"DEBUG: Tab click on {tab_id}")
        except Exception as e:
            self.status_label.config(text=f"Click error: {e}")
            print(f"ERROR: Click error: {e}")
    
    def on_tab_drag(self, event):
        """Handle tab drag."""
        try:
            if self._drag_data["start_tab"] is None:
                return
                
            dx = abs(event.x - self._drag_data["start_x"])
            dy = abs(event.y - self._drag_data["start_y"])
            
            if not self._drag_data["dragging"] and (dx > 5 or dy > 5):
                self._drag_data["dragging"] = True
                self.status_label.config(text=f"Dragging tab {self._drag_data['start_tab']}")
                self.notebook.config(cursor="hand2")
                print(f"DEBUG: Started dragging tab {self._drag_data['start_tab']}")
                
        except Exception as e:
            print(f"ERROR: Drag error: {e}")
    
    def on_tab_release(self, event):
        """Handle tab release."""
        try:
            if not self._drag_data.get("dragging", False):
                self.reset_drag_state()
                return
                
            # Find target tab
            target_tab = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
            
            if target_tab != "" and target_tab != self._drag_data["start_tab"]:
                source_idx = self._drag_data["start_tab"]
                target_idx = int(target_tab)
                
                self.status_label.config(text=f"Moving tab {source_idx} to {target_idx}")
                print(f"DEBUG: Moving tab {source_idx} to {target_idx}")
                
                # Perform the move
                self.move_tab(source_idx, target_idx)
            else:
                self.status_label.config(text="No valid move target")
                
        except Exception as e:
            self.status_label.config(text=f"Release error: {e}")
            print(f"ERROR: Release error: {e}")
        finally:
            self.reset_drag_state()
    
    def move_tab(self, from_idx, to_idx):
        """Move a tab and test if bindings survive."""
        try:
            # Get tab info before manipulation
            tab_text = self.notebook.tab(from_idx, "text")
            tab_frame = self.notebook.nametowidget(self.notebook.tabs()[from_idx])
            
            print(f"DEBUG: Before move - bindings test...")
            self.test_bindings()
            
            # Perform the move
            self.notebook.forget(from_idx)
            
            # Adjust target index if needed
            if from_idx < to_idx:
                to_idx -= 1
                
            self.notebook.insert(to_idx, tab_frame, text=tab_text)
            self.notebook.select(to_idx)
            
            print(f"DEBUG: After move - bindings test...")
            self.test_bindings()
            
            # Re-establish bindings
            self.root.after_idle(self.setup_drag_bindings)
            
        except Exception as e:
            self.status_label.config(text=f"Move error: {e}")
            print(f"ERROR: Move error: {e}")
    
    def reset_drag_state(self):
        """Reset drag state."""
        self._drag_data = {
            "dragging": False,
            "start_tab": None,
            "start_x": 0,
            "start_y": 0
        }
        self.notebook.config(cursor="")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = DragTestApp()
    app.run()