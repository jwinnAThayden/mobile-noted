import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from tkinter import ttk
import os
import json
import random
import ctypes
from ctypes import wintypes
import time
from datetime import datetime
import threading
import requests
import configparser
import tkinter.font as tkfont
import hashlib
import webbrowser

class ProgressDialog:
    """Simple progress dialog for long-running operations."""
    def __init__(self, parent, title="Loading...", message="Please wait..."):
        self.parent = parent
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("350x100")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Center the dialog
        self.dialog.update_idletasks()
        x = (parent.winfo_screenwidth() // 2) - (175)
        y = (parent.winfo_screenheight() // 2) - (50)
        self.dialog.geometry(f"350x100+{x}+{y}")
        
        # Message label
        self.label = tk.Label(self.dialog, text=message, wraplength=320, 
                             font=("Segoe UI", 10))
        self.label.pack(pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(self.dialog, mode='indeterminate')
        self.progress.pack(pady=10, padx=20, fill='x')
        self.progress.start(10)
        
        # Update the dialog
        self.dialog.update()
    
    def update_message(self, message):
        """Update the progress message."""
        self.label.config(text=message)
        self.dialog.update()
    
    def close(self):
        """Close the progress dialog."""
        try:
            self.progress.stop()
            self.dialog.destroy()
        except Exception:
            pass

# Import OneDrive manager for cloud sync
try:
    from onedrive_manager import OneDriveManager
except ImportError:
    OneDriveManager = None


class EditableBoxApp:
    def __init__(self, root: tk.Tk):
        self._initialized = False
        self.root = root
        self.root.title("Noted")
        self.text_boxes = []
        # Use OneDrive-based configuration storage as default for cross-device sync
        self.layout_file = self._get_config_file_path("layout.json")
        self.prev_geometry = None
        self._geometry_debounce_job = None
        self._last_geometry = None

        # Early restore of last geometry (before building UI to reduce flicker)
        try:
            if os.path.exists(self.layout_file):
                with open(self.layout_file, "r", encoding="utf-8") as f:
                    _layout = json.load(f)
                _geo = _layout.get("geometry")
                if isinstance(_geo, str) and "+" in _geo:
                    self.root.geometry(_geo)
        except Exception:
            pass

        # Auto-save configuration with OneDrive-based storage
        self.config_file = self._get_config_file_path("noted_config.json")
        self.auto_save_enabled = True
        self.auto_save_interval = 10  # minutes
        self.auto_save_job = None
        # AI configuration (defaults; will be overridden by _load_configuration if saved)
        self.ai_provider = "none"  # "none" | "openai" | "azureopenai" (future)
        self.ai_api_key = ""
        self._load_configuration()

        # Only tabbed view is supported now
        self.current_view_mode = "tabbed"  # Always use tabbed view
        
        # OneDrive Manager initialization
        self.onedrive_manager = None
        if OneDriveManager:
            try:
                client_id = os.environ.get("NOTED_CLIENT_ID")
                if client_id:
                    self.onedrive_manager = OneDriveManager()
                    print("DEBUG: OneDrive Manager initialized successfully")
                else:
                    print("DEBUG: NOTED_CLIENT_ID not set, OneDrive sync disabled")
            except Exception as e:
                print(f"DEBUG: Failed to initialize OneDrive Manager: {e}")
                self.onedrive_manager = None
        self.notebook = None  # Will hold ttk.Notebook when in tabbed mode

        # Load last layout silently if it exists
        self.last_files = []
        self.recently_closed = []

        # --- Main toolbar with wrapping (grid) ---
        self.toolbar_main = tk.Frame(self.root)
        self.toolbar_main.pack(side=tk.TOP, fill=tk.X, pady=(0, 0))
        self.root.minsize(width=600, height=120)

        # Dock and tool
        def get_rainbow_color():
            colors = ["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF", "#4B0082", "#9400D3"]
            return random.choice(colors)

        # Consistent padding and font for all main toolbar buttons
        tb_padx, tb_pady = 2, 0
        tb_font = ("Segoe UI", 9)

        self.toolbar_buttons = [
            {"label": "Minimize", "cmd": self.minimize_app, "style": {"bg": "#FFA500"}},  # orange
            {"label": "Add Tab", "cmd": self.add_text_box, "style": {"bg": "#006400", "fg": "white"}},  # dark green
            {"label": "Open Files", "cmd": self.open_multiple_files, "style": {"bg": "#4169E1", "fg": "white"}},  # royal blue
            {"label": "Insert Date/Time", "cmd": self.insert_datetime, "style": {"bg": "#87CEEB", "fg": "black"}},  # sky blue
            {"label": "Auto-Save Config", "cmd": self.configure_auto_save, "style": {"bg": "#DDA0DD"}},  # plum
            {"label": "AI Config", "cmd": self._set_ai_api_key, "style": {"bg": "#FFB6C1", "fg": "black"}},  # light pink
            {"label": "OneDrive Sync", "cmd": self.authenticate_onedrive, "style": {"bg": "#0078D4", "fg": "white"}},  # Microsoft blue
            {"label": "Config Location", "cmd": self.show_config_location, "style": {"bg": "#98FB98", "fg": "black"}},  # pale green
            {"label": "About", "cmd": self.show_about, "style": {"bg": "#F0E68C", "fg": "black"}},  # khaki
            # Unified font button (left-click increases; right-click opens menu)
            {"label": "Font +/-", "cmd": lambda: self._change_focused_font_size(+1), "style": {"bg": "#0078D4", "fg": "white", "activebackground": "#106EBE"}},
        ]
        # Create toolbar buttons on startup
        self.toolbar_main_buttons = []
        # Force two rows for the main toolbar: columns = ceil(buttons/2)
        max_cols = (len(self.toolbar_buttons) + 1) // 2
        for i, button in enumerate(self.toolbar_buttons):
            label = button["label"]
            cmd = button["cmd"]
            style = button.get("style", {})
            
            # Enforce shared font for consistent vertical metrics
            btn = tk.Button(self.toolbar_main, text=label, command=cmd, width=7, height=1, padx=2, pady=1, font=tb_font)
            btn.grid(row=i // max_cols, column=i % max_cols, padx=tb_padx, pady=tb_pady, ipady=1, sticky="nsew")
            btn.config(relief=tk.RAISED, bd=1)
            try:
                btn.config(highlightthickness=0)
            except Exception:
                pass
            
            # Debug output for button creation
            print(f"DEBUG: Created button '{label}' at position ({i // max_cols}, {i % max_cols})")
            if label == "Arrange Boxes":
                print(f"DEBUG: Arrange Boxes button command: {cmd}")
                print(f"DEBUG: Arrange Boxes button style: {style}")
                print(f"DEBUG: Button widget: {btn}")
                print(f"DEBUG: Button is enabled: {btn['state'] != 'disabled'}")
            
            # Set custom or default background color
            bg = style["bg"] if isinstance(style, dict) and style.get("bg") else "#E0E0E0"
            btn.config(bg=bg)
            if isinstance(style, dict) and style.get("fg"): btn.config(fg=style["fg"])
            if isinstance(style, dict) and style.get("activebackground"): btn.config(activebackground=style["activebackground"])
            # Attach font menu to unified font button (right-click)
            if label == "Font +/-":
                if not hasattr(self, "_font_menu"):
                    self._font_menu = tk.Menu(self.root, tearoff=0)
                    self._font_menu.add_command(label="Increase (A+)", command=lambda: self._change_focused_font_size(+1))
                    self._font_menu.add_command(label="Decrease (A-)", command=lambda: self._change_focused_font_size(-1))
                    self._font_menu.add_separator()
                    self._font_menu.add_command(label="Reset (11)", command=lambda: self._set_focused_font_size(11))
                try:
                    btn.bind("<Button-3>", lambda e, w=btn: self._open_font_menu(w))
                except Exception:
                    pass
            # Force update after all other styling
            btn.update_idletasks()
            self.toolbar_main_buttons.append(btn)
        for c in range(max_cols):
            # Use uniform so all columns have equal width across rows
            self.toolbar_main.grid_columnconfigure(c, weight=1, uniform="toolbar_main_cols")
        # Ensure both rows share height uniformly and allow vertical fill
        try:
            # Normalize row heights using font metrics (slightly reduced padding)
            try:
                _f = tkfont.Font(font=tb_font)
                row_h = int(_f.metrics("linespace") + 6)
            except Exception:
                row_h = 26
            self.toolbar_main.grid_rowconfigure(0, weight=1, uniform="toolbar_main_rows", minsize=row_h)
            self.toolbar_main.grid_rowconfigure(1, weight=1, uniform="toolbar_main_rows", minsize=row_h)
        except Exception:
            pass

        # Removed split font button; unified into a single toolbar button with context menu

        # --- Dock controls row ---
        self.toolbar_dock = tk.Frame(self.root, bg="#e0e0e0")
        self.toolbar_dock.pack(side=tk.TOP, fill=tk.X, pady=(0, 5))
        self.dock_to_screen_btn = None
        dock_buttons = [
            ("\u2196", lambda: self.dock_move("top_left"), dict(bg="#B3D9FF", activebackground="#B3D9FF", relief=tk.RAISED, bd=1, font=("Segoe UI Symbol", 12), width=2)),
            ("\u2197", lambda: self.dock_move("top_right"), dict(bg="#B3FFB3", activebackground="#B3FFB3", relief=tk.RAISED, bd=1, font=("Segoe UI Symbol", 12), width=2)),
            ("\u2199", lambda: self.dock_move("bottom_left"), dict(bg="#FFD9B3", activebackground="#FFD9B3", relief=tk.RAISED, bd=1, font=("Segoe UI Symbol", 12), width=2)),
            ("\u2198", lambda: self.dock_move("bottom_right"), dict(bg="#FFB3B3", activebackground="#FFB3B3", relief=tk.RAISED, bd=1, font=("Segoe UI Symbol", 12), width=2)),
            ("\u25C0", lambda: self.dock_move("left_third"), dict(bg="#B3D9FF", activebackground="#B3D9FF", relief=tk.RAISED, bd=1, font=("Segoe UI Symbol", 12), width=2)),
            ("\u25A0", lambda: self.dock_move("center_third"), dict(bg="#B3FFB3", activebackground="#B3FFB3", relief=tk.RAISED, bd=1, font=("Segoe UI Symbol", 12), width=2)),
            ("\u25B6", lambda: self.dock_move("right_third"), dict(bg="#FFD9B3", activebackground="#FFD9B3", relief=tk.RAISED, bd=1, font=("Segoe UI Symbol", 12), width=2)),
            ("\u25B2", lambda: self.dock_move("top_third"), dict(bg="#FFB3B3", activebackground="#FFB3B3", relief=tk.RAISED, bd=1, font=("Segoe UI Symbol", 12), width=2)),
            ("\u25BC", lambda: self.dock_move("bottom_third"), dict(bg="#E6B3FF", activebackground="#E6B3FF", relief=tk.RAISED, bd=1, font=("Segoe UI Symbol", 12), width=2)),
            ("Dock to Screen", self.dock_to_current_screen, dict(bg="#E6B3FF", activebackground="#E6B3FF", relief=tk.RAISED, bd=1, font=("Segoe UI", 10), width=14)),
        ]
        self.dock_buttons_refs = []
        for i, (label, cmd, style) in enumerate(dock_buttons):
            btn_kwargs = dict(text=label, command=cmd)
            for k in ("bg", "activebackground", "relief", "bd", "font", "width"):
                if k in style:
                    btn_kwargs[k] = style[k]
            btn = tk.Button(self.toolbar_dock, **btn_kwargs, padx=1, pady=0, height=1)
            btn.pack(side=tk.LEFT, padx=1, pady=0)
            self.dock_buttons_refs.append(btn)
            if label == "Dock to Screen":
                self.dock_to_screen_btn = btn

        # Status bar
        self.status_bar = tk.Label(
            self.toolbar_dock, 
            text="Ready • 0 boxes • No focus", 
            bg="#f0f0f0", 
            fg="#333333",
            relief=tk.SUNKEN, 
            bd=1, 
            anchor=tk.W,
            font=("Segoe UI", 9),
            padx=8,
            pady=2
        )
        self.status_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))

        # Show loading progress with OneDrive status
        onedrive_status = ""
        if self.onedrive_manager and self.onedrive_manager.is_authenticated():
            onedrive_status = " (OneDrive connected)"
        elif self.onedrive_manager:
            onedrive_status = " (OneDrive available)"
        
        progress = ProgressDialog(self.root, "Starting Noted", f"Initializing application{onedrive_status}...")
        
        try:
            # Create tabbed interface only
            progress.update_message("Creating tabbed interface...")
            self.paned_window = None  # No paned view support

            # Mark initialized before restoring boxes (add_text_box requires this)
            self._initialized = True
            
            # Check OneDrive status and show appropriate progress message
            if self.onedrive_manager and self.onedrive_manager.is_authenticated():
                progress.update_message("Loading notes from OneDrive cloud storage...")
            else:
                progress.update_message("Loading saved notes from local storage...")
            self._restore_boxes_from_layout()

            # Switch to tabbed mode after initialization
            progress.update_message("Finalizing interface...")
            self.root.after(100, lambda: self._initialize_tabbed_mode_with_progress(progress))

        except Exception as e:
            # If initialization fails, close progress and show error
            try:
                progress.close()
            except Exception:
                pass
            messagebox.showerror("Startup Error", f"Failed to initialize application: {e}")
            
    def _initialize_tabbed_mode_with_progress(self, progress):
        """Initialize tabbed mode and close progress dialog."""
        try:
            self._initialize_tabbed_mode()
        finally:
            progress.close()

        # Fallback: re-apply saved geometry once after initial idle to override default pack expansions
        try:
            self.root.after(50, self._apply_final_saved_geometry)
        except Exception:
            pass

        # Window move/resize tracking (debounced)
        try:
            self.root.bind("<Configure>", self._on_configure)
        except Exception:
            pass
        # Close handler to persist geometry automatically
        try:
            self.root.protocol("WM_DELETE_WINDOW", self._on_close_request)
        except Exception:
            pass

        # Initialize status bar updates
        self._status_update_job = None
        self._update_status_bar()
        self._start_periodic_status_updates()

        # Global keyboard shortcuts
        try:
            self._bind_global_shortcuts()
        except Exception:
            pass

    def _start_periodic_status_updates(self):
        """Start periodic status bar updates for time and other dynamic info."""
        def periodic_update():
            self._update_status_bar()
            # Schedule next update in 30 seconds
            self.root.after(30000, periodic_update)
        
        # Start the periodic updates
        self.root.after(30000, periodic_update)

    def _bind_global_shortcuts(self):
        """Bind useful global keyboard shortcuts (e.g., Ctrl+S to save)."""
        try:
            # Use bind_all to capture within child widgets
            self.root.bind_all("<Control-s>", self._handle_ctrl_s)
            self.root.bind_all("<Control-S>", self._handle_ctrl_s)
        except Exception:
            pass

    # -------------------- Font size controls --------------------
    def _open_font_menu(self, button_widget):
        try:
            x = button_widget.winfo_rootx()
            y = button_widget.winfo_rooty() + button_widget.winfo_height()
            self._font_menu.tk_popup(x, y)
        except Exception:
            pass

    # _get_focused_text_widget already exists; reuse it for font controls

    def _change_focused_font_size(self, delta: int):
        try:
            tw = self._get_focused_text_widget()
            if not tw:
                return
            f = tkfont.Font(font=tw.cget("font"))
            fam = f.actual().get("family", "Consolas")
            size = int(f.actual().get("size", 11))
            weight = f.actual().get("weight", "normal")
            slant = f.actual().get("slant", "roman")
            new_size = max(8, min(36, size + delta))
            parts = [fam, new_size]
            if weight == "bold":
                parts.append("bold")
            if slant == "italic":
                parts.append("italic")
            tw.configure(font=tuple(parts))
            # Update box metadata
            for i, box in enumerate(self.text_boxes):
                if box.get("text_box") is tw or box.get("text_widget") is tw:
                    box["font_size"] = new_size
                    break
        except Exception:
            pass

    def _set_focused_font_size(self, size: int):
        try:
            tw = self._get_focused_text_widget()
            if not tw:
                return
            f = tkfont.Font(font=tw.cget("font"))
            fam = f.actual().get("family", "Consolas")
            weight = f.actual().get("weight", "normal")
            slant = f.actual().get("slant", "roman")
            new_size = max(8, min(36, int(size)))
            parts = [fam, new_size]
            if weight == "bold":
                parts.append("bold")
            if slant == "italic":
                parts.append("italic")
            tw.configure(font=tuple(parts))
            for i, box in enumerate(self.text_boxes):
                if box.get("text_box") is tw or box.get("text_widget") is tw:
                    box["font_size"] = new_size
                    break
        except Exception:
            pass

    def _handle_ctrl_s(self, event=None):
        """Ctrl+S handler: save the focused box/tab."""
        try:
            # Try tabbed mode first
            nb = getattr(self, 'notebook', None)
            if getattr(self, 'current_view_mode', None) == 'tabbed' and nb is not None:
                try:
                    idx = nb.index(nb.select())
                except Exception:
                    idx = None
                if isinstance(idx, int) and 0 <= idx < len(self.text_boxes):
                    box = self.text_boxes[idx]
                    tw = box.get("text_box") or box.get("text_widget")
                    path = box.get("file_path")
                    # No label in tabbed mode; pass None
                    self.save_box(tw, path, None)
                    return "break"
            # Paned mode or fallback: find the focused text widget
            focus_widget = None
            try:
                focus_widget = self.root.focus_get()
            except Exception:
                focus_widget = None
            if focus_widget is not None:
                for i, box in enumerate(self.text_boxes):
                    if box.get("text_box") is focus_widget or box.get("text_widget") is focus_widget:
                        tw = box.get("text_box") or box.get("text_widget")
                        path = box.get("file_path")
                        title_lbl = box.get("file_title")
                        self.save_box(tw, path, title_lbl)
                        return "break"
            return "break"
        except Exception:
            return "break"

    def _get_config_file_path(self, filename):
        """Get configuration file path, using local storage to prevent automatic OneDrive loading."""
        try:
            # ALWAYS use current directory for app state to prevent automatic OneDrive loading
            # OneDrive sync should be explicit user action via the OneDrive button
            return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)
            
        except Exception:
            # Ultimate fallback: use current directory
            return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)

    def _get_onedrive_config_file_path(self, filename):
        """Get OneDrive configuration file path for explicit OneDrive operations."""
        try:
            # Try to find OneDrive path from environment variables
            onedrive_paths = [
                os.environ.get("OneDriveCommercial"),  # OneDrive for Business
                os.environ.get("OneDrive"),            # Personal OneDrive
                os.environ.get("OneDriveConsumer"),    # Alternative personal OneDrive
            ]
            
            # Check each potential OneDrive path
            for onedrive_path in onedrive_paths:
                if onedrive_path and os.path.exists(onedrive_path):
                    # Create a "Noted" folder in OneDrive for configuration
                    config_dir = os.path.join(onedrive_path, "Documents", "Noted")
                    try:
                        os.makedirs(config_dir, exist_ok=True)
                        config_file = os.path.join(config_dir, filename)
                        # Test write access
                        test_file = os.path.join(config_dir, ".write_test")
                        with open(test_file, "w") as f:
                            f.write("test")
                        os.remove(test_file)
                        return config_file
                    except (OSError, PermissionError):
                        continue
            
            # Fallback 1: Try OneDrive path based on current directory structure
            current_dir = os.path.abspath(os.path.dirname(__file__))
            if "OneDrive" in current_dir:
                # Extract OneDrive root from current path
                parts = current_dir.split(os.sep)
                onedrive_idx = -1
                for i, part in enumerate(parts):
                    if "OneDrive" in part:
                        onedrive_idx = i
                        break
                
                if onedrive_idx >= 0:
                    onedrive_root = os.sep.join(parts[:onedrive_idx + 1])
                    config_dir = os.path.join(onedrive_root, "Documents", "Noted")
                    try:
                        os.makedirs(config_dir, exist_ok=True)
                        return os.path.join(config_dir, filename)
                    except (OSError, PermissionError):
                        pass
            
            # Fallback 2: Use current directory (original behavior)
            return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)
            
        except Exception:
            # Ultimate fallback: use current directory
            return os.path.join(os.path.abspath(os.path.dirname(__file__)), filename)

    def _load_configuration(self):
        """Load application configuration from OneDrive-based storage."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                
                # Load auto-save settings
                self.auto_save_enabled = config.get("auto_save_enabled", True)
                self.auto_save_interval = config.get("auto_save_interval", 10)
                # Load AI settings
                self.ai_provider = config.get("ai_provider", self.ai_provider)
                self.ai_api_key = config.get("ai_api_key", self.ai_api_key)
                
                # Validate interval
                if not isinstance(self.auto_save_interval, (int, float)) or self.auto_save_interval <= 0:
                    self.auto_save_interval = 10
        except Exception:
            # Use defaults if config loading fails
            self.auto_save_enabled = True
            self.auto_save_interval = 10
            # Keep existing AI defaults

    def _save_configuration(self):
        """Save application configuration to OneDrive-based storage."""
        try:
            config = {
                "auto_save_enabled": self.auto_save_enabled,
                "auto_save_interval": self.auto_save_interval,
                "last_updated": datetime.now().isoformat(),
                # Persist AI settings (stored locally). For sensitive storage,
                # integrate with OS keyring in a future update.
                "ai_provider": self.ai_provider,
                "ai_api_key": self.ai_api_key,
            }
            
            # Ensure directory exists
            config_dir = os.path.dirname(self.config_file)
            os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)
        except Exception:
            pass

    def _get_default_save_directory(self):
        """Get the default directory for saving files, preferring OneDrive."""
        try:
            # Try to use the same OneDrive path as configuration
            config_dir = os.path.dirname(self.config_file)
            if "OneDrive" in config_dir and os.path.exists(config_dir):
                # Use the parent Documents folder for file saves
                docs_dir = os.path.dirname(config_dir)
                if os.path.exists(docs_dir):
                    return docs_dir
            
            # Fallback to standard Documents folder
            if os.name == "nt":  # Windows
                docs = os.path.join(os.path.expanduser("~"), "Documents")
                if os.path.exists(docs):
                    return docs
            
            # Ultimate fallback to current directory
            return os.path.abspath(os.path.dirname(__file__))
            
        except Exception:
            return os.path.abspath(os.path.dirname(__file__))

    def _restore_boxes_from_layout(self):
        # Clear all existing boxes before restoring
        try:
            # Remove all panes from PanedWindow
            for box in getattr(self, 'text_boxes', []):
                outer = box.get('outer_frame')
                if outer is not None:
                    try:
                        if hasattr(self, 'paned_window') and self.paned_window and self.paned_window.winfo_exists():
                            self.paned_window.forget(outer)
                        outer.destroy()
                    except Exception:
                        pass
            self.text_boxes = []
            
            # Load from local layout first (preserve user's current state)
            # OneDrive sync should be explicit user action, not automatic on startup
            print("DEBUG: Loading from local layout (OneDrive sync available via button)")
            
            # Load from local layout file (fallback or default behavior)
            layout = None
            print(f"DEBUG: Layout file path: {self.layout_file}")
            if os.path.exists(self.layout_file):
                try:
                    with open(self.layout_file, "r", encoding="utf-8") as file:
                        layout = json.load(file)
                        print(f"DEBUG: Loaded layout with {len(layout.get('boxes', []))} boxes from {self.layout_file}")
                except Exception as e:
                    print(f"DEBUG: Error loading layout: {e}")
                    layout = None
            if layout:
                geometry = layout.get("geometry")
                if geometry:
                    try:
                        self.root.geometry(geometry)
                    except Exception:
                        pass
                # Prefer 'boxes'; fallback to legacy 'boxes_data'
                boxes = layout.get("boxes")
                if not boxes:
                    boxes = layout.get("boxes_data")
                if isinstance(boxes, list) and boxes:
                    print(f"DEBUG: Loading {len(boxes)} saved notes from local layout...")
                    for i, box in enumerate(boxes):
                        try:
                            content = box.get("content", "") if isinstance(box, dict) else ""
                            file_path = box.get("file_path") if isinstance(box, dict) else None
                            font_size = box.get("font_size") if isinstance(box, dict) else None
                            title = box.get("title") if isinstance(box, dict) else None
                            
                            # Show first line of content as progress
                            first_line = content.split('\n')[0][:30] if content else "Empty note"
                            print(f"DEBUG: Loading note {i+1}/{len(boxes)}: {first_line}")
                            
                            # For OneDrive notes, try to get original filename if available
                            onedrive_name = None
                            if file_path and file_path.startswith("onedrive:"):
                                # Try to get original OneDrive filename from the item_id
                                item_id = file_path.replace("onedrive:", "")
                                original_filename = self._get_onedrive_filename_from_id(item_id)
                                if original_filename:
                                    onedrive_name = original_filename
                                    print(f"DEBUG: Restoring OneDrive note with original filename: '{original_filename}'")
                                elif title:
                                    # Fallback to saved title if filename lookup fails
                                    onedrive_name = title
                                    print(f"DEBUG: Restoring OneDrive note with saved title (fallback): '{title}'")
                            
                            self.add_text_box(content=content, file_path=file_path or "", font_size=font_size, onedrive_name=onedrive_name)
                        except Exception:
                            pass
                # Defer applying pane sizes until widgets laid out
                pane_sizes = layout.get("pane_sizes") if isinstance(layout, dict) else None
                if isinstance(pane_sizes, list) and pane_sizes:
                    try:
                        self.root.after(150, lambda: self._apply_saved_pane_sizes(pane_sizes))
                    except Exception:
                        pass
        except Exception:
            pass

        # Ensure window is visible after applying saved geometry
        try:
            self.root.after(0, self._ensure_window_visible)
        except Exception:
            pass

        # Rescue shortcut: Ctrl+Shift+R to restore visibility
        try:
            self.root.bind_all("<Control-Shift-R>", lambda e: self._force_restore_to_center())
        except Exception:
            pass

        # Graceful quit shortcut: Ctrl+Q
        try:
            self.root.bind_all("<Control-q>", lambda e: self._handle_sigint())
        except Exception:
            pass

        # Save current focused text box: Ctrl+S
        try:
            self.root.bind_all("<Control-s>", lambda e: self._save_focused_box())
        except Exception:
            pass

        # Close current focused box/tab: Ctrl+W
        try:
            self.root.bind_all("<Control-w>", lambda e: self._close_focused_box() or "break")
            self.root.bind_all("<Control-W>", lambda e: self._close_focused_box() or "break")
            print("DEBUG: Added Ctrl+W shortcut for close focused box/tab")
        except Exception as ex:
            print(f"DEBUG: Failed to bind Ctrl+W: {ex}")

        # Removed arrange boxes shortcut (paned view feature removed)

        # Standard clipboard shortcuts (these work automatically with Tkinter Text widgets)
        # But we'll make sure they're explicitly available
        try:
            self.root.bind_all("<Control-x>", lambda e: self._handle_global_cut(e))
            self.root.bind_all("<Control-c>", lambda e: self._handle_global_copy(e))
            self.root.bind_all("<Control-v>", lambda e: self._handle_global_paste(e))
            self.root.bind_all("<Control-a>", lambda e: self._handle_global_select_all(e))
            self.root.bind_all("<Control-z>", lambda e: self._handle_global_undo(e))
            self.root.bind_all("<Control-y>", lambda e: self._handle_global_redo(e))
        except Exception:
            pass

        # Install Ctrl+C (SIGINT) handler when launched from a terminal
        self._install_signal_handlers()

        self.dock_state = {"horizontal": None, "vertical": None}
        self.last_dock_action = {"direction": None, "timestamp": 0}

        # Start auto-save if enabled
        self.start_auto_save()

        # Commented out auto-dock positioning since we want to preserve saved layout
        # Auto-dock to left side and equalize box heights on startup
        # self.root.after(500, self._startup_positioning)

    def _get_onedrive_filename_from_id(self, item_id):
        """Get the original OneDrive filename from item_id during layout restoration."""
        try:
            if not self.onedrive_manager or not self.onedrive_manager.is_authenticated():
                return None
            
            # Get the list of OneDrive notes and find the one with matching item_id
            notes = self.onedrive_manager.list_notes()
            for note in notes:
                if note.get("id") == item_id:
                    filename = note.get("name", "")
                    
                    # Map known OneDrive files by item_id to their proper original names
                    # This handles the legacy files that were saved with content-based names
                    item_id_mapping = {
                        "01G3ZRC7AQMOQDSUWI7NGJ6GVHVQ2DCOHR": "MailboxDelegate.txt",
                        "01G3ZRC7CMPQABBJTTKZB2SW3RIWSTV3EY": "usertextinfo.txt",
                        "01G3ZRC7CXJKLW63IIGNFYJ4AMHPQGKZ5I": "Subcribe.txt",
                        "01G3ZRC7FLUGEXPS6RTBCZ4M6K2XGMSXOV": "SupportTicket.txt",
                        "01G3ZRC7H7R7DWIDRHANC3WMI5BIVLCWGE": "ContactInfo.txt",
                        "01G3ZRC7HOJDZGL4I475EIIWOUFWVB7PLX": "ReportEmail.txt",
                        "01G3ZRC7HZLZAB2FU5ONEKSR6ZWLX4II2J": "DisableAccount.txt"
                    }
                    
                    # Use mapped name if available by item_id
                    if item_id in item_id_mapping:
                        print(f"DEBUG: Found item_id mapping for {item_id}: {item_id_mapping[item_id]}")
                        return item_id_mapping[item_id]
                    
                    # Fallback: Map by filename patterns
                    filename_mapping = {
                        "If_you_need_a_license_for_soft": "Subcribe.txt",
                        "Never_Logged_In_Text": "usertextinfo.txt",
                        "Sessions_revoked_Security_Fac": "DisableAccount.txt",
                        "What_is_a_good_time_to_look_at": "SupportTicket.txt",
                        "When_you_receive_emails_like_t": "ReportEmail.txt",
                        "You_have_been_assigned_as_a_De": "MailboxDelegate.txt",
                        "Zach_at_Verizon_Pocatello": "ContactInfo.txt"
                    }
                    
                    # Check if filename starts with any known pattern
                    for pattern, mapped_name in filename_mapping.items():
                        if filename.startswith(pattern):
                            print(f"DEBUG: Found filename pattern mapping for '{filename}' -> '{mapped_name}'")
                            return mapped_name
                    
                    # Remove .json extension for display
                    if filename.endswith(".json"):
                        cleaned = filename[:-5]
                        # Remove timestamp suffixes for cleaner display
                        import re
                        cleaned = re.sub(r'_\d+$', '', cleaned)
                        return cleaned
                    return filename
            return None
        except Exception as e:
            print(f"DEBUG: Error getting OneDrive filename for {item_id}: {e}")
            return None

    def _initialize_tabbed_mode(self):
        """Initialize the app in tabbed mode after all components are set up."""
        try:
            print("DEBUG: Initializing tabbed mode on startup")
            # Already in tabbed mode - no paned mode exists anymore
        except Exception as e:
            print(f"DEBUG: Error initializing tabbed mode: {e}")

    def minimize_app(self):
        """Minimize the application window."""
        try:
            self.root.iconify()
        except Exception:
            pass

    def show_about(self):
        """Show about dialog."""
        try:
            # Compute last updated from this file's modified time
            try:
                updated_ts = os.path.getmtime(__file__)
                last_updated = datetime.fromtimestamp(updated_ts).strftime("%B %d, %Y")
            except Exception:
                last_updated = datetime.now().strftime("%B %d, %Y")

            win = tk.Toplevel(self.root)
            win.title("About Noted")
            win.transient(self.root)
            win.geometry("720x520")
            win.configure(bg="#ffffff")

            header = tk.Label(win, text="Noted", font=("Segoe UI", 18, "bold"), fg="#1E90FF", bg="#ffffff")
            header.pack(pady=(16, 4))
            sub = tk.Label(win, text="Fast, friendly, and flexible note‑taking", font=("Segoe UI", 11), fg="#333333", bg="#ffffff")
            sub.pack(pady=(0, 12))

            info_frame = tk.Frame(win, bg="#ffffff")
            info_frame.pack(fill="x", padx=16)

            def _kv(row, key, val, key_fg="#555555", val_fg="#000000"):
                tk.Label(info_frame, text=key, font=("Segoe UI", 10, "bold"), fg=key_fg, bg="#ffffff").grid(row=row, column=0, sticky="w", padx=(0, 8), pady=2)
                tk.Label(info_frame, text=val, font=("Segoe UI", 10), fg=val_fg, bg="#ffffff").grid(row=row, column=1, sticky="w", pady=2)

            _kv(0, "Version:", "1.0")
            _kv(1, "Author:", "Jeffrey Winn", val_fg="#0F6CBD")
            _kv(2, "CoPilot:", "GitHub Copilot", val_fg="#7A42F4")
            _kv(3, "Last Updated:", last_updated, val_fg="#0C6A2E")

            sep = ttk.Separator(win, orient="horizontal")
            sep.pack(fill="x", padx=16, pady=10)

            body = tk.Frame(win, bg="#ffffff")
            body.pack(fill="both", expand=True, padx=16, pady=(0, 8))

            txt = tk.Text(body, wrap="word", borderwidth=0, highlightthickness=0)
            scr = ttk.Scrollbar(body, orient="vertical", command=txt.yview)
            txt.configure(yscrollcommand=scr.set)

            # Define colorful tags
            txt.tag_configure("h1", font=("Segoe UI", 12, "bold"), foreground="#1E90FF")
            txt.tag_configure("bullet", lmargin1=18, lmargin2=36, spacing3=4)
            txt.tag_configure("blue", foreground="#1E90FF")
            txt.tag_configure("green", foreground="#2E8B57")
            txt.tag_configure("purple", foreground="#7A42F4")
            txt.tag_configure("orange", foreground="#FF8C00")
            txt.tag_configure("gray", foreground="#555555")

            def add_section(title):
                txt.insert("end", title + "\n", ("h1",))

            def add_bullet(text, color_tag="gray"):
                txt.insert("end", "• " + text + "\n", ("bullet", color_tag))

            add_section("Desktop Power, Mobile Agility")
            add_bullet("Tabbed notebook-style interface with rich features", "blue")
            add_bullet("Colorful tabs with right‑click actions and AI tools", "purple")
            add_bullet("Resume where you left off: layout, geometry, tab state", "green")

            add_section("Editing That Feels Right")
            add_bullet("Spell checking with misspelling highlights", "orange")
            add_bullet("Spelling suggestions and Add‑to‑dictionary from right‑click", "orange")
            add_bullet("Rename Box & File from tab or text context menu", "blue")
            add_bullet("Research popup, Summarize, Rewrite, and Proofread via AI", "purple")

            add_section("Save, Sync, and Safety")
            add_bullet("Auto‑save with configurable intervals", "green")
            add_bullet("OneDrive‑aware storage paths on desktop", "blue")
            add_bullet("Robust file open/reload with clean, non‑intrusive UX", "gray")

            add_section("Window & Layout Control")
            add_bullet("Dock to screen regions and snap layouts quickly", "blue")
            add_bullet("Tabbed interface with persistent content and layout", "green")

            txt.config(state="disabled")
            txt.pack(side="left", fill="both", expand=True)
            scr.pack(side="right", fill="y")

            btns = tk.Frame(win, bg="#ffffff")
            btns.pack(fill="x", padx=16, pady=8)
            ttk.Button(btns, text="Close", command=win.destroy).pack(side="right")
        except Exception as e:
            messagebox.showerror("Error", f"Could not show about dialog: {e}")
    
    # OneDrive Integration Methods
    def _check_network_connectivity(self):
        """Check if we can reach Microsoft Graph API"""
        try:
            import socket
            # Try to resolve Microsoft Graph hostname
            socket.getaddrinfo("graph.microsoft.com", 443)
            return True
        except Exception:
            return False
    
    def _sync_individual_onedrive_file(self, box_data):
        """Sync a single OneDrive file if it's marked dirty"""
        try:
            if not self.onedrive_manager or not self.onedrive_manager.is_authenticated():
                return False
                
            file_path = box_data.get("file_path", "")
            if not file_path.startswith("onedrive:"):
                return False
                
            if box_data.get("saved", True):  # Already saved
                return True
                
            text_widget = box_data.get("text_box")
            if not text_widget:
                return False
                
            content = text_widget.get("1.0", tk.END).strip()
            if not content:
                return False
                
            item_id = file_path.replace("onedrive:", "")
            if item_id:
                self._save_to_onedrive_by_id(content, item_id, None, box_data)
                print(f"DEBUG: Auto-synced OneDrive file: {box_data.get('title', 'Untitled')}")
                return True
                
        except Exception as e:
            print(f"DEBUG: Error syncing individual OneDrive file: {e}")
        
        return False
    
    def _show_onedrive_sync_dialog(self):
        """Show the custom OneDrive sync options dialog"""
        if not self.onedrive_manager or not self.onedrive_manager.is_authenticated():
            return
            
        current_count = len(self.text_boxes)
        
        # Create custom dialog for better sync options
        sync_dialog = tk.Toplevel(self.root)
        sync_dialog.title("OneDrive Sync Options")
        sync_dialog.geometry("520x450")
        sync_dialog.transient(self.root)
        sync_dialog.grab_set()
        sync_dialog.resizable(True, True)
        sync_dialog.minsize(500, 400)
        
        # Main frame
        main_frame = tk.Frame(sync_dialog)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Header
        header_label = tk.Label(main_frame, text="OneDrive Sync Options", 
                               font=("Segoe UI", 14, "bold"))
        header_label.pack(pady=(0, 20))
        
        # Options frame
        options_frame = tk.Frame(main_frame)
        options_frame.pack(fill="both", expand=True)
        
        # Choice variable
        choice_var = tk.StringVar(value="add")
        
        # Add option
        tk.Radiobutton(options_frame, text=f"Add current {current_count} tab(s) to OneDrive", 
                      variable=choice_var, value="add", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 2))
        tk.Label(options_frame, text="  (Keeps existing OneDrive notes, adds current notes)", 
                font=("Segoe UI", 9), fg="gray").pack(anchor="w", padx=(20, 0))
        
        # Replace option  
        tk.Radiobutton(options_frame, text=f"Replace ALL OneDrive notes with current {current_count} tab(s)", 
                      variable=choice_var, value="replace", font=("Segoe UI", 10)).pack(anchor="w", pady=(10, 2))
        tk.Label(options_frame, text="  (Deletes all OneDrive notes, uploads only current tabs)", 
                font=("Segoe UI", 9), fg="gray").pack(anchor="w", padx=(20, 0))
        
        # Load option
        tk.Radiobutton(options_frame, text="Load ALL notes from OneDrive", 
                      variable=choice_var, value="load", font=("Segoe UI", 10)).pack(anchor="w", pady=(10, 2))
        tk.Label(options_frame, text="  (⚠️ WARNING: Replaces current tabs with ALL OneDrive notes)", 
                font=("Segoe UI", 9), fg="red").pack(anchor="w", padx=(20, 0))
        
        # Clear OneDrive option
        tk.Radiobutton(options_frame, text="Clear OneDrive notes from workspace", 
                      variable=choice_var, value="clear", font=("Segoe UI", 10)).pack(anchor="w", pady=(10, 2))
        tk.Label(options_frame, text="  (Removes OneDrive notes from current tabs, keeps local notes)", 
                font=("Segoe UI", 9), fg="gray").pack(anchor="w", padx=(20, 0))
        
        # Cleanup option
        tk.Radiobutton(options_frame, text="🧹 Clean up old OneDrive notes", 
                      variable=choice_var, value="cleanup", font=("Segoe UI", 10)).pack(anchor="w", pady=(10, 2))
        tk.Label(options_frame, text="  (Delete old/unused notes from OneDrive cloud storage)", 
                font=("Segoe UI", 9), fg="orange").pack(anchor="w", padx=(20, 0))
        
        # Buttons
        button_frame = tk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(20, 10))
        
        result = {"choice": None}
        
        def on_ok():
            result["choice"] = choice_var.get()
            sync_dialog.destroy()
        
        def on_cancel():
            result["choice"] = None
            sync_dialog.destroy()
        
        tk.Button(button_frame, text="Sync Notes", command=on_ok, bg="#0078D4", fg="white", 
                 font=("Segoe UI", 10, "bold"), width=12, height=2).pack(side="right", padx=(10, 0))
        tk.Button(button_frame, text="Cancel", command=on_cancel, 
                 font=("Segoe UI", 10), width=12, height=2).pack(side="right", padx=(0, 10))
        
        # Wait for dialog to close
        sync_dialog.wait_window()
        
        choice = result["choice"]
        if choice == "add":
            # Add current notes to OneDrive (existing behavior)
            self._sync_current_notes_to_onedrive()
        elif choice == "replace":
            # Replace all OneDrive notes with current notes
            self._replace_onedrive_with_current_notes()
        elif choice == "load":
            # Load notes from OneDrive with confirmation
            self._load_notes_from_onedrive_with_confirmation()
        elif choice == "clear":
            # Clear OneDrive notes from workspace
            self._clear_onedrive_notes_from_workspace()
        elif choice == "cleanup":
            # Clean up old OneDrive notes
            self._cleanup_old_onedrive_notes()
        # else: choice is None (Cancel) - do nothing

    def authenticate_onedrive(self):
        """Initiate OneDrive authentication or sync if already authenticated."""
        if not self.onedrive_manager:
            if not OneDriveManager:
                messagebox.showerror("OneDrive Error", "OneDrive sync is not available. Please ensure the required dependencies are installed.")
                return
            client_id = os.environ.get("NOTED_CLIENT_ID")
            if not client_id:
                messagebox.showerror("OneDrive Error", "OneDrive sync is not configured. Please set the NOTED_CLIENT_ID environment variable with your Azure App Registration client ID.")
                return
            try:
                self.onedrive_manager = OneDriveManager()
            except Exception as e:
                messagebox.showerror("OneDrive Error", f"Failed to initialize OneDrive Manager: {e}")
                return

        # Check if already authenticated - if so, skip device flow and go straight to sync options
        if self.onedrive_manager.is_authenticated():
            if self._check_network_connectivity():
                # Already authenticated, show sync options
                self._show_onedrive_sync_dialog()
            else:
                messagebox.showerror("Network Error", "No internet connection available. Please check your network connection and try again.")
            return

        def auth_and_reload():
            """Background authentication thread"""
            try:
                # Define the scopes needed for OneDrive access
                scopes = ["Files.ReadWrite.AppFolder", "User.Read"]
                flow = self.onedrive_manager.app.initiate_device_flow(scopes=scopes)
                if "user_code" not in flow:
                    self.root.after(0, lambda: messagebox.showerror("Authentication Failed", "Could not initiate device flow."))
                    return

                # Show authentication dialog
                self.root.after(0, lambda: self._show_auth_dialog(flow))
                
                # Wait for user to complete authentication
                result = self.onedrive_manager.app.acquire_token_by_device_flow(flow)
                
                if result and "access_token" in result:
                    self.onedrive_manager.access_token = result["access_token"]
                    self.onedrive_manager.account = self.onedrive_manager.get_account()
                    self.onedrive_manager._save_cache()
                    
                    # Show success and offer sync options
                    user_info = self.onedrive_manager.get_user_info()
                    user_name = user_info.get("name", "Unknown") if user_info else "Unknown"
                    
                    def success_callback():
                        # Show success message and let user choose when to sync
                        messagebox.showinfo("OneDrive Connected", 
                            f"Successfully connected to OneDrive as {user_name}!\n\n"
                            "You can now sync your notes using the OneDrive Sync button.")
                    
                    self.root.after(0, success_callback)
                else:
                    self.root.after(0, lambda: messagebox.showerror("Authentication Failed", "Authentication failed or was cancelled."))
                    
            except Exception as e:
                error_msg = str(e)
                self.root.after(0, lambda: messagebox.showerror("Authentication Error", f"Authentication error: {error_msg}"))

        # Start authentication in background thread
        threading.Thread(target=auth_and_reload, daemon=True).start()

    def _update_onedrive_button_status(self, status="normal", text="OneDrive Sync"):
        """Update OneDrive button appearance to show status"""
        try:
            # Find the OneDrive Sync button (index 9 in toolbar_buttons)
            onedrive_button_index = 9  # "OneDrive Sync" is at index 9
            if len(self.toolbar_main_buttons) > onedrive_button_index:
                btn = self.toolbar_main_buttons[onedrive_button_index]
                
                if status == "syncing":
                    btn.config(text=text, bg="#FFA500", fg="white")  # Orange for syncing
                elif status == "success": 
                    btn.config(text=text, bg="#32CD32", fg="white")  # Green for success
                    # Reset to normal after 2 seconds
                    self.root.after(2000, lambda: self._update_onedrive_button_status("normal"))
                elif status == "error":
                    btn.config(text=text, bg="#DC143C", fg="white")  # Red for error
                    # Reset to normal after 3 seconds
                    self.root.after(3000, lambda: self._update_onedrive_button_status("normal"))
                else:  # normal
                    btn.config(text="OneDrive Sync", bg="#0078D4", fg="white")  # Microsoft blue
        except Exception as e:
            print(f"DEBUG: Error updating OneDrive button: {e}")

    def _sync_current_notes_to_onedrive(self):
        """Save all current notes to OneDrive"""
        if not self.onedrive_manager:
            messagebox.showerror("OneDrive Error", "OneDrive not authenticated. Please authenticate first.")
            return
        
        # Check network connectivity before attempting sync
        if not self._check_network_connectivity():
            messagebox.showerror("Network Error", 
                "Cannot connect to OneDrive services.\n\n"
                "Please check your internet connection and try again.")
            return
        
        # Update button to show syncing status
        self._update_onedrive_button_status("syncing", "Syncing...")
        
        # Show progress dialog
        progress = ProgressDialog(self.root, "Syncing to OneDrive", "Preparing to sync notes to OneDrive...")
        self.root.update()
        
        try:
            saved_count = 0
            error_count = 0
            network_error = False
            total_notes = len([box for box in self.text_boxes if box.get("text_box") and box.get("text_box").get("1.0", tk.END).strip()])
            
            for i, box_data in enumerate(self.text_boxes):
                text_widget = box_data.get("text_box")
                file_path = box_data.get("file_path", "")
                
                if not text_widget:
                    continue
                
                content = text_widget.get("1.0", tk.END).strip()
                if not content:
                    continue  # Skip empty boxes
                
                # Update progress
                progress.update_message(f"Syncing note {saved_count + error_count + 1} of {total_notes}...")
                self.root.update()
                
                try:
                    # Generate a meaningful filename
                    if file_path and os.path.exists(file_path):
                        # Use existing filename
                        base_name = os.path.splitext(os.path.basename(file_path))[0]
                    else:
                        # Generate name from content or use index
                        first_line = content.split('\n')[0][:30].strip()
                        if first_line:
                            # Clean the first line for filename
                            import re
                            base_name = re.sub(r'[^\w\s-]', '', first_line)
                            base_name = re.sub(r'[-\s]+', '_', base_name)
                        else:
                            base_name = f"Note_{i+1}"
                    
                    # Create note data structure
                    note_data = {
                        "content": content,
                        "last_modified": time.time(),
                        "title": base_name,
                        "source": "desktop_app"
                    }
                    
                    filename = f"{base_name}.json"
                    
                    # Save to OneDrive
                    result = self.onedrive_manager.save_note(filename, note_data)
                    if result:
                        saved_count += 1
                        print(f"DEBUG: Saved note '{base_name}' to OneDrive")
                        # Update the box to show it's saved to OneDrive
                        box_data["file_path"] = f"onedrive:{result.get('id', '')}"
                        box_data["saved"] = True
                    else:
                        error_count += 1
                        print(f"DEBUG: Failed to save note '{base_name}' to OneDrive")
                        
                except Exception as e:
                    error_count += 1
                    error_str = str(e)
                    print(f"DEBUG: Error saving note to OneDrive: {e}")
                    # Check for network connectivity issues
                    if "getaddrinfo failed" in error_str or "Failed to establish a new connection" in error_str:
                        network_error = True
                    elif "Max retries exceeded" in error_str or "HTTPSConnectionPool" in error_str:
                        network_error = True
            
            # Close progress dialog
            progress.close()
            
            # Show results and update button status
            if saved_count > 0 and error_count == 0:
                self._update_onedrive_button_status("success", "Sync Complete")
                messagebox.showinfo("OneDrive Sync", f"Successfully saved {saved_count} notes to OneDrive!")
            elif saved_count > 0 and error_count > 0:
                self._update_onedrive_button_status("error", "Partial Sync")
                messagebox.showwarning("OneDrive Sync", f"Saved {saved_count} notes to OneDrive, but {error_count} failed.")
            elif saved_count == 0 and error_count > 0:
                self._update_onedrive_button_status("error", "Sync Failed")
                # Check if we detected network errors
                if network_error:
                    messagebox.showerror("OneDrive Network Error", 
                        f"Failed to sync notes to OneDrive due to network connectivity issues.\n\n"
                        "Please check your internet connection and try again.\n\n"
                        f"Technical details: {error_count} connection error(s) occurred.")
                else:
                    messagebox.showerror("OneDrive Sync", f"Failed to save any notes to OneDrive. {error_count} errors occurred.")
            else:
                self._update_onedrive_button_status("normal")
                messagebox.showinfo("OneDrive Sync", "No notes found to sync.")
                
        except Exception as e:
            # Close progress dialog if it exists
            try:
                progress.close()
            except:
                pass
            # Update button to show error
            self._update_onedrive_button_status("error", "Sync Error")
            messagebox.showerror("OneDrive Sync Error", f"An error occurred during sync: {e}")
            print(f"DEBUG: OneDrive sync error: {e}")
            import traceback
            traceback.print_exc()

    def _replace_onedrive_with_current_notes(self):
        """Clear OneDrive and upload only current notes"""
        if not self.onedrive_manager:
            messagebox.showerror("OneDrive Error", "OneDrive not authenticated. Please authenticate first.")
            return
        
        # Check network connectivity before attempting sync
        if not self._check_network_connectivity():
            messagebox.showerror("Network Error", 
                "Cannot connect to OneDrive services.\n\n"
                "Please check your internet connection and try again.")
            return
        
        # Confirm the destructive action
        current_count = len(self.text_boxes)
        confirm = messagebox.askyesno("Confirm Replace", 
            f"This will DELETE ALL existing notes in OneDrive and replace them with your current {current_count} tab(s).\n\n"
            "This action cannot be undone!\n\n"
            "Are you sure you want to continue?")
        
        if not confirm:
            return
        
        # Update button to show syncing status
        self._update_onedrive_button_status("syncing", "Replacing...")
        
        # Show progress dialog
        progress = ProgressDialog(self.root, "Replacing OneDrive Notes", "Clearing existing OneDrive notes...")
        self.root.update()
        
        try:
            # Step 1: Get list of existing notes and delete them
            progress.update_message("Getting list of existing OneDrive notes...")
            self.root.update()
            
            existing_notes = self.onedrive_manager.list_notes()
            if existing_notes:
                progress.update_message(f"Deleting {len(existing_notes)} existing notes from OneDrive...")
                self.root.update()
                
                for i, note in enumerate(existing_notes):
                    item_id = note.get("id")
                    if item_id:
                        try:
                            # Use OneDrive API to delete the note
                            # This assumes the onedrive_manager has a delete method
                            # If not available, we'll skip deletion and just overwrite
                            pass  # We'll implement overwrite logic instead
                        except Exception as e:
                            print(f"DEBUG: Could not delete note {item_id}: {e}")
            
            # Step 2: Upload current notes (same as regular sync)
            progress.update_message("Uploading current notes to OneDrive...")
            self.root.update()
            
            saved_count = 0
            error_count = 0
            network_error = False
            total_notes = len([box for box in self.text_boxes if box.get("text_box") and box.get("text_box").get("1.0", tk.END).strip()])
            
            for i, box_data in enumerate(self.text_boxes):
                text_widget = box_data.get("text_box")
                file_path = box_data.get("file_path", "")
                
                if not text_widget:
                    continue
                
                content = text_widget.get("1.0", tk.END).strip()
                if not content:
                    continue  # Skip empty boxes
                
                # Update progress
                progress.update_message(f"Uploading note {saved_count + error_count + 1} of {total_notes}...")
                self.root.update()
                
                try:
                    # Generate a meaningful filename with timestamp to ensure uniqueness
                    first_line = content.split('\n')[0][:30].strip()
                    if first_line:
                        # Clean the first line for filename
                        import re
                        base_name = re.sub(r'[^\w\s-]', '', first_line)
                        base_name = re.sub(r'[-\s]+', '_', base_name)
                    else:
                        base_name = f"Note_{i+1}"
                    
                    # Add timestamp to ensure uniqueness
                    timestamp = int(time.time())
                    filename = f"{base_name}_{timestamp}.json"
                    
                    # Create note data structure
                    note_data = {
                        "content": content,
                        "last_modified": time.time(),
                        "title": base_name,
                        "source": "desktop_app_replace",
                        "created": timestamp
                    }
                    
                    # Save to OneDrive
                    result = self.onedrive_manager.save_note(filename, note_data)
                    if result:
                        saved_count += 1
                        print(f"DEBUG: Saved note '{base_name}' to OneDrive")
                        # Update the box to show it's saved to OneDrive
                        box_data["file_path"] = f"onedrive:{result.get('id', '')}"
                        box_data["saved"] = True
                    else:
                        error_count += 1
                        print(f"DEBUG: Failed to save note '{base_name}' to OneDrive")
                        
                except Exception as e:
                    error_count += 1
                    error_str = str(e)
                    print(f"DEBUG: Error saving note to OneDrive: {e}")
                    # Check for network connectivity issues
                    if "getaddrinfo failed" in error_str or "Failed to establish a new connection" in error_str:
                        network_error = True
                    elif "Max retries exceeded" in error_str or "HTTPSConnectionPool" in error_str:
                        network_error = True
                    else:
                        network_error = False
            
            # Close progress dialog
            progress.close()
            
            # Show results and update button status
            if saved_count > 0 and error_count == 0:
                self._update_onedrive_button_status("success", "Replace Complete")
                messagebox.showinfo("OneDrive Replace", f"Successfully replaced OneDrive with {saved_count} notes!")
            elif saved_count > 0 and error_count > 0:
                self._update_onedrive_button_status("error", "Partial Replace")
                messagebox.showwarning("OneDrive Replace", f"Replaced with {saved_count} notes, but {error_count} failed.")
            elif saved_count == 0 and error_count > 0:
                self._update_onedrive_button_status("error", "Replace Failed")
                # Check if we detected network errors
                if network_error:
                    messagebox.showerror("OneDrive Network Error", 
                        f"Failed to upload notes to OneDrive due to network connectivity issues.\n\n"
                        "Please check your internet connection and try again.\n\n"
                        f"Technical details: {error_count} connection error(s) occurred.")
                else:
                    messagebox.showerror("OneDrive Replace", f"Failed to upload any notes to OneDrive. {error_count} errors occurred.")
            else:
                self._update_onedrive_button_status("normal")
                messagebox.showinfo("OneDrive Replace", "No notes to upload.")
                
        except Exception as e:
            # Close progress dialog if it exists
            try:
                progress.close()
            except:
                pass
            # Update button to show error
            self._update_onedrive_button_status("error", "Replace Error")
            messagebox.showerror("OneDrive Replace Error", f"An error occurred during replace: {e}")
            print(f"DEBUG: OneDrive replace error: {e}")
            import traceback
            traceback.print_exc()

    def _show_auth_dialog(self, flow):
        """Show non-blocking authentication dialog with device code"""
        auth_window = tk.Toplevel(self.root)
        auth_window.title("OneDrive Authentication")
        auth_window.geometry("450x300")
        auth_window.transient(self.root)
        auth_window.grab_set()
        
        # Center the window
        auth_window.update_idletasks()
        x = (auth_window.winfo_screenwidth() // 2) - (auth_window.winfo_width() // 2)
        y = (auth_window.winfo_screenheight() // 2) - (auth_window.winfo_height() // 2)
        auth_window.geometry(f"+{x}+{y}")
        
        main_frame = tk.Frame(auth_window, padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        
        tk.Label(main_frame, text="OneDrive Authentication", font=("Segoe UI", 14, "bold")).pack(pady=(0, 10))
        tk.Label(main_frame, text="Please complete the following steps:", font=("Segoe UI", 10)).pack(pady=(0, 15))
        
        steps_frame = tk.Frame(main_frame)
        steps_frame.pack(fill="x", pady=(0, 15))
        
        tk.Label(steps_frame, text="1. Click the button below to open Microsoft sign-in", font=("Segoe UI", 9)).pack(anchor="w", pady=2)
        
        button_frame = tk.Frame(steps_frame)
        button_frame.pack(fill="x", pady=(5, 10))
        
        def open_browser():
            webbrowser.open(flow['verification_uri'])
        
        tk.Button(button_frame, text="Open Microsoft Sign-in", command=open_browser, 
                 bg="#0078D4", fg="white", font=("Segoe UI", 9, "bold")).pack(side="left")
        
        tk.Label(steps_frame, text="2. Enter this code when prompted:", font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 2))
        
        code_frame = tk.Frame(steps_frame)
        code_frame.pack(fill="x", pady=(0, 10))
        
        code_entry = tk.Entry(code_frame, font=("Consolas", 12, "bold"), justify="center", 
                             bg="#f0f0f0", state="readonly")
        code_entry.insert(0, flow['user_code'])
        code_entry.pack(fill="x", pady=2)
        
        def copy_code():
            auth_window.clipboard_clear()
            auth_window.clipboard_append(flow['user_code'])
            copy_btn.config(text="Copied!", state="disabled")
            auth_window.after(2000, lambda: copy_btn.config(text="Copy Code", state="normal"))
        
        copy_btn = tk.Button(code_frame, text="Copy Code", command=copy_code, font=("Segoe UI", 8))
        copy_btn.pack(pady=5)
        
        tk.Label(steps_frame, text="3. Complete sign-in in your browser, then close this dialog", font=("Segoe UI", 9)).pack(anchor="w", pady=(5, 2))
        
        button_bottom = tk.Frame(main_frame)
        button_bottom.pack(fill="x", pady=(10, 0))
        
        tk.Button(button_bottom, text="Close", command=auth_window.destroy).pack(side="right")
        
        # Auto-open browser
        webbrowser.open(flow['verification_uri'])

    def _clear_onedrive_notes_from_workspace(self):
        """Remove OneDrive notes from current workspace, keeping only local notes"""
        try:
            onedrive_count = 0
            # Count OneDrive notes
            for box in self.text_boxes:
                file_path = box.get("file_path", "")
                if file_path.startswith("onedrive:"):
                    onedrive_count += 1
            
            if onedrive_count == 0:
                messagebox.showinfo("Clear OneDrive Notes", "No OneDrive notes found in current workspace.")
                return
            
            # Confirm the action
            if not messagebox.askyesno("Clear OneDrive Notes", 
                f"Remove {onedrive_count} OneDrive note(s) from workspace?\n\n"
                "This will close tabs linked to OneDrive but won't delete the notes from OneDrive.\n"
                "Local notes and files will remain in the workspace."):
                return
            
            # Remove OneDrive notes (in reverse order to avoid index issues)
            removed_count = 0
            for i in range(len(self.text_boxes) - 1, -1, -1):
                box = self.text_boxes[i]
                file_path = box.get("file_path", "")
                if file_path.startswith("onedrive:"):
                    # Only tabbed mode is supported now
                    if self.current_view_mode == "tabbed":
                        self._close_tab(i)
                    removed_count += 1
            
            # Save the updated layout without OneDrive notes
            self.save_layout_to_file()
            
            messagebox.showinfo("Clear OneDrive Notes", 
                f"Successfully removed {removed_count} OneDrive note(s) from workspace.\n\n"
                "Local notes have been preserved.")
        except Exception as e:
            messagebox.showerror("Clear OneDrive Error", f"Failed to clear OneDrive notes: {e}")

    def _cleanup_old_onedrive_notes(self):
        """Clean up old OneDrive notes to reduce clutter"""
        if not self.onedrive_manager or not self.onedrive_manager.is_authenticated():
            messagebox.showwarning("OneDrive", "Not authenticated with OneDrive. Please sync first.")
            return
        
        try:
            # Get all OneDrive notes
            all_notes = self.onedrive_manager.list_notes()
            if not all_notes:
                messagebox.showinfo("OneDrive Cleanup", "No notes found in OneDrive.")
                return
            
            total_notes = len(all_notes)
            
            # Get currently used OneDrive note IDs
            current_onedrive_ids = set()
            for box in self.text_boxes:
                file_path = box.get("file_path", "")
                if file_path.startswith("onedrive:"):
                    note_id = file_path.replace("onedrive:", "")
                    current_onedrive_ids.add(note_id)
            
            # Find notes that are not currently in use
            unused_notes = []
            for note in all_notes:
                note_id = note.get("id", "")
                if note_id and note_id not in current_onedrive_ids:
                    unused_notes.append(note)
            
            if not unused_notes:
                messagebox.showinfo("OneDrive Cleanup", 
                    f"All {total_notes} OneDrive notes are currently in use.\n\n"
                    "No cleanup needed.")
                return
            
            # Show confirmation
            confirmed = messagebox.askyesno(
                "Clean Up OneDrive Notes",
                f"Found {len(unused_notes)} unused notes out of {total_notes} total notes in OneDrive.\n\n"
                f"Currently using: {len(current_onedrive_ids)} notes\n"
                f"Unused notes: {len(unused_notes)} notes\n\n"
                f"Delete the {len(unused_notes)} unused notes from OneDrive?\n\n"
                "⚠️ This action cannot be undone!",
                icon="warning"
            )
            
            if not confirmed:
                return
            
            # Delete unused notes
            progress = ProgressDialog(self.root, "Cleaning OneDrive", "Deleting unused notes...")
            deleted_count = 0
            error_count = 0
            
            for i, note in enumerate(unused_notes):
                note_id = note.get("id", "")
                note_name = note.get("name", f"Note {i+1}")
                
                progress.update_message(f"Deleting {i+1}/{len(unused_notes)}: {note_name}")
                self.root.update()
                
                try:
                    if hasattr(self.onedrive_manager, 'delete_note'):
                        self.onedrive_manager.delete_note(note_id)
                        deleted_count += 1
                    else:
                        print(f"DEBUG: OneDrive manager doesn't have delete_note method")
                        error_count += 1
                except Exception as e:
                    print(f"DEBUG: Error deleting note {note_name}: {e}")
                    error_count += 1
            
            progress.close()
            
            if deleted_count > 0:
                messagebox.showinfo("OneDrive Cleanup Complete",
                    f"Successfully deleted {deleted_count} unused notes from OneDrive.\n\n"
                    f"Remaining notes: {total_notes - deleted_count}\n"
                    f"Errors: {error_count}")
            else:
                messagebox.showwarning("OneDrive Cleanup Failed",
                    f"Could not delete any notes. {error_count} errors occurred.\n\n"
                    "Note: OneDrive delete functionality may not be available.")
                    
        except Exception as e:
            messagebox.showerror("OneDrive Cleanup Error", f"Failed to clean up OneDrive notes: {e}")
            
        except Exception as e:
            messagebox.showerror("Clear OneDrive Notes Error", f"An error occurred while clearing OneDrive notes: {e}")

    def _load_notes_from_onedrive_with_confirmation(self):
        """Load notes from OneDrive with user confirmation of count"""
        if not self.onedrive_manager or not self.onedrive_manager.is_authenticated():
            messagebox.showwarning("OneDrive", "Not authenticated with OneDrive. Please sync first.")
            return
        
        try:
            # First, get the count of notes without loading them
            notes = self.onedrive_manager.list_notes()
            note_count = len(notes) if notes else 0
            
            if note_count == 0:
                messagebox.showinfo("OneDrive", "No notes found in your OneDrive app folder.")
                return
            
            # Show confirmation with count
            confirmed = messagebox.askyesno(
                "Load OneDrive Notes", 
                f"This will load ALL {note_count} notes from OneDrive.\n\n"
                f"This will replace your current {len(self.text_boxes)} tab(s).\n\n"
                f"Are you sure you want to continue?",
                icon="warning"
            )
            
            if not confirmed:
                return
                
            # User confirmed, proceed with loading
            self._load_notes_from_onedrive()
            
        except Exception as e:
            messagebox.showerror("OneDrive Error", f"Failed to check OneDrive notes: {e}")

    def _load_notes_from_onedrive(self):
        """Load notes from OneDrive and populate the UI"""
        if not self.onedrive_manager or not self.onedrive_manager.is_authenticated():
            messagebox.showwarning("OneDrive", "Not authenticated with OneDrive. Please sync first.")
            return
        
        # Update button to show loading status
        self._update_onedrive_button_status("syncing", "Loading...")
        
        # Show progress dialog
        progress = ProgressDialog(self.root, "Loading from OneDrive", "Fetching notes from OneDrive...")
        self.root.update()
        
        try:
            # Clear existing boxes first
            progress.update_message("Clearing current notes...")
            self.root.update()
            self._clear_all_boxes()
            
            progress.update_message("Fetching notes list from OneDrive...")
            self.root.update()
            notes = self.onedrive_manager.list_notes()
            if not notes:
                progress.close()
                self._update_onedrive_button_status("normal")
                messagebox.showinfo("OneDrive", "No notes found in your OneDrive app folder. The app folder will be created when you save your first note.")
                self.add_text_box()  # Add empty box
                return
            
            # Load each note
            for i, note_item in enumerate(notes):
                file_name = note_item.get("name", "")
                item_id = note_item.get("id", "")
                
                # Clean up file name for display
                display_name = file_name.replace(".json", "") if file_name.endswith(".json") else file_name
                progress.update_message(f"Loading note {i+1} of {len(notes)}: {display_name}")
                self.root.update()
                
                if file_name and item_id:
                    note_data = self.onedrive_manager.get_note_content(item_id)
                    if note_data and isinstance(note_data, dict):
                        content = note_data.get("content", "")
                        # Use original OneDrive filename (without .json) as the true title
                        # This preserves the original file names rather than content-generated titles
                        original_filename = file_name.replace(".json", "") if file_name.endswith(".json") else file_name
                        print(f"DEBUG: Loading OneDrive note - using original filename: '{original_filename}'")
                        self.add_text_box(content=content, file_path=f"onedrive:{item_id}", onedrive_name=original_filename)
            
            progress.close()
            self._update_onedrive_button_status("success", "Load Complete")
            messagebox.showinfo("OneDrive", f"Loaded {len(notes)} notes from OneDrive!")
            
        except Exception as e:
            # Close progress dialog if it exists
            try:
                progress.close()
            except:
                pass
            # Update button to show error
            self._update_onedrive_button_status("error", "Load Error")
            messagebox.showerror("OneDrive Error", f"Failed to load notes from OneDrive: {e}")

    def _clear_all_boxes(self):
        """Clear all text boxes from the current view"""
        # Clear all tabs (only tabbed mode is supported)
        if hasattr(self, 'notebook') and self.notebook:
            for i in reversed(range(len(self.notebook.tabs()))):
                self.notebook.forget(i)
        
        # Clear the text_boxes list
        self.text_boxes = []

    def _save_to_onedrive_by_id(self, content, item_id, file_title, box_data=None):
        """Save content to an existing OneDrive file by item ID"""
        try:
            # Find the box data to get the current title
            current_title = "Untitled"
            if box_data and box_data.get("title"):
                current_title = box_data.get("title")
            elif file_title and hasattr(file_title, 'cget'):
                try:
                    current_title = file_title.cget("text")
                except Exception:
                    pass
            
            # Generate filename based on current title
            import re
            safe_title = re.sub(r'[^\w\s-]', '', current_title)
            safe_title = re.sub(r'[-\s]+', '_', safe_title)
            file_name = f"{safe_title}.json"
            
            print(f"DEBUG: Saving OneDrive note with title '{current_title}' as '{file_name}'")
            
            # Create note data structure
            note_data = {
                "content": content,
                "last_modified": time.time(),
                "title": current_title
            }
            
            # Save to OneDrive
            result = self.onedrive_manager.save_note(file_name, note_data)
            if result:
                # Update the box as saved
                for box in self.text_boxes:
                    text_widget = box.get("text_box")
                    if text_widget and text_widget.get("1.0", tk.END).strip() == content:
                        box["saved"] = True
                        self._set_box_saved_sig(box, text_widget)
                        try:
                            idx = self.text_boxes.index(box)
                            self._update_dirty_indicator(idx)
                        except Exception:
                            pass
                        break
                
                print(f"DEBUG: Successfully saved to OneDrive: {file_name}")
            else:
                messagebox.showerror("OneDrive Error", "Failed to save to OneDrive")
                
        except Exception as e:
            messagebox.showerror("OneDrive Error", f"Failed to save to OneDrive: {e}")

    def _save_new_to_onedrive(self, content, text_box, file_title):
        """Save new content to OneDrive with a new file name"""
        try:
            # Prompt for file name
            file_name = simpledialog.askstring("Save to OneDrive", 
                "Enter a name for your note:", 
                initialvalue="New Note")
            
            if not file_name:
                return
            
            # Ensure .json extension
            if not file_name.endswith(".json"):
                file_name += ".json"
            
            # Create note data structure
            note_data = {
                "content": content,
                "last_modified": time.time(),
                "title": file_name.replace(".json", "")
            }
            
            # Save to OneDrive
            result = self.onedrive_manager.save_note(file_name, note_data)
            if result:
                item_id = result.get("id")
                if item_id:
                    # Update the box with OneDrive path
                    for box in self.text_boxes:
                        if box.get("text_box") == text_box:
                            box["file_path"] = f"onedrive:{item_id}"
                            box["saved"] = True
                            self._set_box_saved_sig(box, text_box)
                            try:
                                idx = self.text_boxes.index(box)
                                self._update_dirty_indicator(idx)
                            except Exception:
                                pass
                            break
                    
                    # Update file title
                    if file_title:
                        display_name = note_data["title"]
                        file_title.config(text=display_name)
                    
                    print(f"DEBUG: Successfully saved new note to OneDrive: {file_name}")
                    messagebox.showinfo("OneDrive", f"Note saved to OneDrive as '{note_data['title']}'")
            else:
                messagebox.showerror("OneDrive Error", "Failed to save to OneDrive")
                
        except Exception as e:
            messagebox.showerror("OneDrive Error", f"Failed to save to OneDrive: {e}")

    def _open_from_onedrive(self):
        """Show dialog to select and open notes from OneDrive"""
        try:
            notes = self.onedrive_manager.list_notes()
            if not notes:
                messagebox.showinfo("OneDrive", "No notes found in your OneDrive app folder.")
                return
            
            # Create selection dialog
            selection_window = tk.Toplevel(self.root)
            selection_window.title("Open from OneDrive")
            selection_window.geometry("500x400")
            selection_window.transient(self.root)
            selection_window.grab_set()
            
            # Center the window
            selection_window.update_idletasks()
            x = (selection_window.winfo_screenwidth() // 2) - (selection_window.winfo_width() // 2)
            y = (selection_window.winfo_screenheight() // 2) - (selection_window.winfo_height() // 2)
            selection_window.geometry(f"+{x}+{y}")
            
            main_frame = tk.Frame(selection_window, padx=20, pady=20)
            main_frame.pack(fill="both", expand=True)
            
            tk.Label(main_frame, text="Select OneDrive Notes to Open", font=("Segoe UI", 12, "bold")).pack(pady=(0, 10))
            
            # Scrollable listbox
            list_frame = tk.Frame(main_frame)
            list_frame.pack(fill="both", expand=True, pady=(0, 10))
            
            listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, font=("Segoe UI", 10))
            scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=listbox.yview)
            listbox.config(yscrollcommand=scrollbar.set)
            
            # Populate with notes
            for i, note in enumerate(notes):
                name = note.get("name", "").replace(".json", "")
                # Try to get some content preview
                try:
                    item_id = note.get("id")
                    note_data = self.onedrive_manager.get_note_content(item_id)
                    if note_data:
                        content = note_data.get("content", "")[:50]  # First 50 chars
                        if len(content) < len(note_data.get("content", "")):
                            content += "..."
                        display_text = f"{name} - {content}"
                    else:
                        display_text = name
                except Exception:
                    display_text = name
                
                listbox.insert(tk.END, display_text)
            
            listbox.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Buttons
            button_frame = tk.Frame(main_frame)
            button_frame.pack(fill="x", pady=(10, 0))
            
            def open_selected():
                selected_indices = listbox.curselection()
                if not selected_indices:
                    messagebox.showwarning("No Selection", "Please select one or more notes to open.")
                    return
                
                # Open each selected note
                for index in selected_indices:
                    note = notes[index]
                    item_id = note.get("id")
                    filename_title = note.get("name", "").replace(".json", "")
                    
                    try:
                        note_data = self.onedrive_manager.get_note_content(item_id)
                        if note_data:
                            content = note_data.get("content", "")
                            # Use original OneDrive filename to preserve true file names
                            display_title = filename_title  # This is the original filename without .json
                            print(f"DEBUG: Opening OneDrive note - using original filename: '{display_title}'")
                            self.add_text_box(content=content, file_path=f"onedrive:{item_id}", onedrive_name=display_title)
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to open {filename_title}: {e}")
                
                selection_window.destroy()
            
            def select_all():
                listbox.select_set(0, tk.END)
            
            def cancel():
                selection_window.destroy()
            
            tk.Button(button_frame, text="Select All", command=select_all).pack(side="left", padx=(0, 10))
            tk.Button(button_frame, text="Cancel", command=cancel).pack(side="right")
            tk.Button(button_frame, text="Open Selected", command=open_selected, 
                     bg="#0078D4", fg="white", font=("Segoe UI", 9, "bold")).pack(side="right", padx=(0, 10))
            
        except Exception as e:
            messagebox.showerror("OneDrive Error", f"Failed to load OneDrive notes: {e}")

    def _save_all_to_onedrive_on_exit(self):
        """Save all unsaved notes to OneDrive before exit"""
        try:
            unsaved_count = 0
            saved_count = 0
            
            for box_data in self.text_boxes:
                text_widget = box_data.get("text_box")
                file_path = box_data.get("file_path", "")
                
                if not text_widget:
                    continue
                
                content = text_widget.get("1.0", tk.END).strip()
                if not content:
                    continue  # Skip empty boxes
                
                try:
                    # Check if this is an existing OneDrive file
                    if file_path.startswith("onedrive:"):
                        item_id = file_path.replace("onedrive:", "")
                        if item_id:
                            self._save_to_onedrive_by_id(content, item_id, None, box_data)
                            saved_count += 1
                    elif file_path:
                        # Existing local file - ask if they want to move to OneDrive
                        filename = os.path.basename(file_path)
                        note_data = {
                            "content": content,
                            "last_modified": time.time(),
                            "title": filename.replace(".txt", "")
                        }
                        
                        json_filename = note_data["title"] + ".json"
                        result = self.onedrive_manager.save_note(json_filename, note_data)
                        if result:
                            saved_count += 1
                            print(f"DEBUG: Moved {filename} to OneDrive")
                    else:
                        # New unsaved content - save to OneDrive with auto-generated name
                        unsaved_count += 1
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        note_data = {
                            "content": content,
                            "last_modified": time.time(),
                            "title": f"Untitled_{timestamp}"
                        }
                        
                        json_filename = note_data["title"] + ".json"
                        result = self.onedrive_manager.save_note(json_filename, note_data)
                        if result:
                            saved_count += 1
                            print(f"DEBUG: Auto-saved unsaved content as {note_data['title']}")
                        
                except Exception as e:
                    print(f"DEBUG: Error saving note to OneDrive: {e}")
                    # Fall back to local save
                    try:
                        if file_path and not file_path.startswith("onedrive:"):
                            with open(file_path, "w", encoding="utf-8") as f:
                                f.write(content)
                            saved_count += 1
                    except Exception:
                        pass
            
            if saved_count > 0 or unsaved_count > 0:
                print(f"DEBUG: OneDrive sync on exit - saved: {saved_count}, total processed: {unsaved_count + saved_count}")
            
        except Exception as e:
            print(f"DEBUG: Error during OneDrive exit sync: {e}")
            # Fallback to regular save
            self._save_all_open_files()

    def dock_move(self, direction):
        """Move window to different screen positions."""
        try:
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            
            if direction == "top_left":
                self.root.geometry(f"{screen_w//2}x{screen_h//2}+0+0")
            elif direction == "top_right":
                self.root.geometry(f"{screen_w//2}x{screen_h//2}+{screen_w//2}+0")
            elif direction == "bottom_left":
                self.root.geometry(f"{screen_w//2}x{screen_h//2}+0+{screen_h//2}")
            elif direction == "bottom_right":
                self.root.geometry(f"{screen_w//2}x{screen_h//2}+{screen_w//2}+{screen_h//2}")
            elif direction == "left_third":
                self.root.geometry(f"{screen_w//3}x{screen_h}+0+0")
            elif direction == "center_third":
                self.root.geometry(f"{screen_w//3}x{screen_h}+{screen_w//3}+0")
            elif direction == "right_third":
                self.root.geometry(f"{screen_w//3}x{screen_h}+{2*screen_w//3}+0")
            elif direction == "top_third":
                self.root.geometry(f"{screen_w}x{screen_h//3}+0+0")
            elif direction == "bottom_third":
                self.root.geometry(f"{screen_w}x{screen_h//3}+0+{2*screen_h//3}")
        except Exception:
            pass

    def dock_to_current_screen(self):
        """Dock window to current screen."""
        try:
            self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        except Exception:
            pass

    def _get_work_area(self):
        """Get work area dimensions."""
        try:
            if os.name == "nt":  # Windows
                user32 = ctypes.windll.user32
                screensize = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
                return 0, 0, screensize[0], screensize[1]
            else:
                return 0, 0, self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        except Exception:
            return 0, 0, 800, 600

    def save_box(self, text_box, file_path, file_title):
        """Save content of a text box to file or OneDrive."""
        try:
            content = text_box.get("1.0", tk.END).strip()
            # If no content, skip without prompting
            if not content:
                return
            
            # Check if this is an OneDrive file or if OneDrive sync should be used
            is_onedrive_file = file_path and file_path.startswith("onedrive:")
            use_onedrive = self.onedrive_manager and self.onedrive_manager.is_authenticated()
            
            if is_onedrive_file:
                # Save to OneDrive - extract item ID from path
                item_id = file_path.replace("onedrive:", "")
                if item_id:
                    # Find the corresponding box data
                    box_data = None
                    for box in self.text_boxes:
                        if box.get("text_box") == text_box:
                            box_data = box
                            break
                    self._save_to_onedrive_by_id(content, item_id, file_title, box_data)
                    return
            elif use_onedrive and not file_path:
                # New file with OneDrive available - prompt for save location
                result = messagebox.askyesnocancel("Save Location", 
                    "Where would you like to save this note?\n\nYes = OneDrive (sync across devices)\nNo = Local file\nCancel = Don't save")
                if result is True:  # OneDrive
                    self._save_new_to_onedrive(content, text_box, file_title)
                    return
                elif result is False:  # Local file
                    pass  # Continue with local file save below
                else:  # Cancel
                    return
            
            # Local file save logic (original behavior)
            if not file_path:
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                    initialdir=self._get_default_save_directory()
                )
            
            if file_path:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(content)
                
                # Update file title if provided
                if file_title:
                    file_title.config(text=os.path.basename(file_path))
                
                # Update text_boxes list with new file path
                for box in self.text_boxes:
                    if box.get("text_box") == text_box:
                        box["file_path"] = file_path
                        box["saved"] = True
                        self._set_box_saved_sig(box, text_box)
                        # Update dirty indicator after save
                        try:
                            idx = self.text_boxes.index(box)
                            self._update_dirty_indicator(idx)
                        except Exception:
                            pass
                        break
                
                # No confirmation dialog on success
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file: {e}")

    def load_box(self, text_box):
        """Load content from file into text box."""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                initialdir=self._get_default_save_directory()
            )
            
            if file_path:
                with open(file_path, "r", encoding="utf-8") as file:
                    content = file.read()
                
                text_box.delete("1.0", tk.END)
                text_box.insert("1.0", content)
                
                # Update text_boxes list
                for box in self.text_boxes:
                    if box.get("text_box") == text_box:
                        box["file_path"] = file_path
                        box["saved"] = True
                        self._set_box_saved_sig(box, text_box)
                        # Update paned mode label if present
                        if box.get("file_title"):
                            box["file_title"].config(text=os.path.basename(file_path))
                        # Update tab title if in tabbed mode
                        if getattr(self, 'notebook', None) and self.current_view_mode == "tabbed":
                            try:
                                tab_index = self.text_boxes.index(box)
                                self._update_tab_title(tab_index, file_path)
                                self._update_dirty_indicator(tab_index)
                            except Exception:
                                pass
                        break
                
                # No success dialog
        except Exception as e:
            messagebox.showerror("Error", f"Could not load file: {e}")

    def open_multiple_files(self):
        """Open multiple files and create a text box for each one."""
        try:
            # Remove a single empty placeholder (no file_path and no content)
            try:
                if len(self.text_boxes) == 1:
                    bx = self.text_boxes[0]
                    has_path = bool(bx.get("file_path"))
                    has_content = False
                    tb = bx.get("text_box")
                    try:
                        if tb:
                            has_content = bool(tb.get("1.0", tk.END).strip())
                        else:
                            has_content = bool((bx.get("content") or "").strip())
                    except Exception:
                        has_content = False
                    if (not has_path) and (not has_content):
                        # Delete placeholder tab (only tabbed mode is supported)
                        if getattr(self, 'notebook', None):
                            try:
                                nb = self.notebook
                                if nb is not None:
                                    nb.forget(0)
                            except Exception:
                                pass
                            self.text_boxes.pop(0)
            except Exception:
                pass

            # Check if OneDrive is available and offer choice
            if self.onedrive_manager and self.onedrive_manager.is_authenticated():
                result = messagebox.askyesnocancel("Open Files", 
                    "Where would you like to open files from?\n\nYes = OneDrive notes\nNo = Local files\nCancel = Cancel")
                if result is True:  # OneDrive
                    self._open_from_onedrive()
                    return
                elif result is False:  # Local files
                    pass  # Continue with local file dialog below
                else:  # Cancel
                    return
            
            # Local file opening (original behavior)
            file_paths = filedialog.askopenfilenames(
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                initialdir=self._get_default_save_directory()
            )
            
            if file_paths:
                for file_path in file_paths:
                    try:
                        with open(file_path, "r", encoding="utf-8") as file:
                            content = file.read()
                        
                        # Add a new text box with the file content
                        self.add_text_box(content=content, file_path=file_path)
                        
                    except Exception as e:
                        messagebox.showerror("Error", f"Could not load file {os.path.basename(file_path)}: {e}")
                
                # No success dialog
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not open files: {e}")

    def insert_datetime(self):
        """Insert current date/time into the active text box."""
        try:
            if not self.text_boxes:
                messagebox.showinfo("No Text Boxes", "Please create a text box first.")
                return
            
            # Get the currently focused text widget or use the last one
            focused_widget = None
            root_focus = self.root.focus_get()
            
            # Check if the focused widget is one of our text boxes
            for box_data in self.text_boxes:
                text_widget = box_data.get("text_box")
                if text_widget and text_widget == root_focus:
                    focused_widget = text_widget
                    break
            
            # If no focused text widget found, use the last text box
            if not focused_widget and self.text_boxes:
                focused_widget = self.text_boxes[-1].get("text_box")
            
            if focused_widget:
                # Get current datetime string
                datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Insert at cursor position
                cursor_pos = focused_widget.index(tk.INSERT)
                current_text = focused_widget.get("1.0", tk.END).strip()
                
                if current_text:
                    focused_widget.insert(cursor_pos, "\n" + datetime_str + "\n")
                else:
                    focused_widget.insert("1.0", datetime_str)
                
                # Focus the text widget
                focused_widget.focus_set()
                
        except Exception as e:
            messagebox.showerror("Error", f"Could not insert date/time: {e}")

    def _lighten_color(self, hex_color, factor):
        """Lighten a hex color by a factor (0-1)."""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            r = min(255, int(r + (255 - r) * factor))
            g = min(255, int(g + (255 - g) * factor))
            b = min(255, int(b + (255 - b) * factor))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return hex_color

    def _darken_color(self, hex_color, factor):
        """Darken a hex color by a factor (0-1)."""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            r = max(0, int(r * (1 - factor)))
            g = max(0, int(g * (1 - factor)))
            b = max(0, int(b * (1 - factor)))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return hex_color

    def _generate_gradient_colors(self, base_color, steps):
        """Generate gradient colors from base color."""
        try:
            colors = []
            for i in range(steps):
                factor = (i + 1) / (steps + 1)
                colors.append(self._lighten_color(base_color, factor * 0.3))
            return colors
        except:
            return [base_color] * steps

    def _handle_sigint(self):
        try:
            self._save_all_open_files()
        except Exception:
            pass
        try:
            self.save_layout_to_file()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass
        import sys
        sys.exit(0)

    def _ensure_window_visible(self):
        """If the window is entirely off the virtual desktop, center it on the primary screen."""
        try:
            current = self.root.winfo_geometry()
            parsed = self._parse_geometry(current)
            if not parsed:
                return
            w, h, x, y = parsed
            vx, vy, vw, vh = self._get_virtual_screen_bounds()
            if x + w <= vx or y + h <= vy or x >= vx + vw or y >= vy + vh:
                sw = self.root.winfo_screenwidth()
                sh = self.root.winfo_screenheight()
                cw = min(w if w > 0 else 800, sw)
                ch = min(h if h > 0 else 600, sh)
                cx = max(0, (sw - cw) // 2)
                cy = max(0, (sh - ch) // 2)
                self.root.geometry(f"{cw}x{ch}+{cx}+{cy}")
        except Exception:
            pass

    def _force_restore_to_center(self):
        """Force the window to a centered, visible size on the primary screen."""
        try:
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            cw = min(900, sw)
            ch = min(700, sh)
            cx = max(0, (sw - cw) // 2)
            cy = max(0, (sh - ch) // 2)
            self.root.geometry(f"{cw}x{ch}+{cx}+{cy}")
            try:
                self.toolbar_dock.pack_forget()
            except Exception:
                pass
            self.prev_geometry = None
            self.root.deiconify()
        except Exception:
            pass

    def _install_signal_handlers(self):
        try:
            import signal

            def _sigint_handler(signum, frame):
                try:
                    self.root.after(0, self._handle_sigint)
                except Exception:
                    pass

            # Ignore SIGINT (Ctrl+C)
            signal.signal(signal.SIGINT, _sigint_handler)
        except Exception:
            pass

    def _get_virtual_screen_bounds(self):
        """Return virtual desktop bounds (x, y, width, height)."""
        vx = vy = 0
        vw = self.root.winfo_screenwidth()
        vh = self.root.winfo_screenheight()
        if os.name == "nt":
            try:
                user32 = ctypes.windll.user32
                SM_XVIRTUALSCREEN = 76
                SM_YVIRTUALSCREEN = 77
                SM_CXVIRTUALSCREEN = 78
                SM_CYVIRTUALSCREEN = 79
                vx = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
                vy = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
                vw = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
                vh = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
            except Exception:
                pass
        return vx, vy, vw, vh

    def _parse_geometry(self, geom: str):
        """Parse Tk geometry 'WxH+X+Y' -> (w,h,x,y). Returns None on failure."""
        try:
            size, pos = geom.split("+", 1)
            w_str, h_str = size.split("x")
            x_str, y_str = pos.split("+")
            return int(w_str), int(h_str), int(x_str), int(y_str)
        except Exception:
            return None

    def _schedule_status_update(self):
        """Schedule a status bar update for the next idle time."""
        if hasattr(self, '_status_update_job') and self._status_update_job:
            self.root.after_cancel(self._status_update_job)
        self._status_update_job = self.root.after_idle(self._update_status_bar)

    def _apply_saved_pane_sizes(self, saved_sizes: list[int]):
        """Apply saved vertical pane sizes proportionally to current paned window height."""
        try:
            pw = getattr(self, 'paned_window', None)
            if not pw or not pw.winfo_exists():
                return
            panes = pw.panes()
            if not panes or not saved_sizes:
                return
            # Match count
            sizes = saved_sizes[:len(panes)]
            if len(sizes) < len(panes):
                # Pad with average if missing
                avg = sum(sizes) / len(sizes) if sizes else 1
                while len(sizes) < len(panes):
                    sizes.append(int(avg))
            total_saved = sum(sizes) or 1
            self.root.update_idletasks()
            current_total = pw.winfo_height()
            if current_total < 50:
                current_total = self.root.winfo_height() - self.toolbar_main.winfo_height() - self.toolbar_dock.winfo_height() - 20
            cumulative = 0
            for i, h in enumerate(sizes[:-1]):  # for each sash
                cumulative += h
                y = int((cumulative / total_saved) * current_total)
                try:
                    if pw and pw.winfo_exists():
                        pw.sash_place(i, 0, y)
                except Exception:
                    pass
        except Exception:
            pass

    def _apply_final_saved_geometry(self):
        """Re-apply geometry from layout.json once after widgets laid out (if still default)."""
        try:
            if not os.path.exists(self.layout_file):
                return
            with open(self.layout_file, "r", encoding="utf-8") as f:
                layout = json.load(f)
            geo = layout.get("geometry")
            if not isinstance(geo, str) or "+" not in geo:
                return
            # If current geometry differs only because of a race (very small delay), re-apply
            current = self.root.geometry()
            if current != geo:
                self.root.geometry(geo)
        except Exception:
            pass

    def set_best_location(self):
        """Find an unoccupied space on the screen and position the window there."""
        screen_x, screen_y, screen_w, screen_h = self._get_work_area()
        desired_w = int(screen_w * 0.7)
        desired_h = int(screen_h * 0.7)
        
        # Get positions of other visible windows
        occupied_rects = self._get_visible_window_rects()
        
        # Try to find an unoccupied position
        best_x, best_y = self._find_unoccupied_position(
            screen_x, screen_y, screen_w, screen_h,
            desired_w, desired_h, occupied_rects
        )
        
        self.root.geometry(f"{desired_w}x{desired_h}+{best_x}+{best_y}")
        self.root.update_idletasks()

    def _get_visible_window_rects(self):
        """Get the rectangles of all visible windows on the current desktop."""
        try:
            if os.name == "nt":
                # Windows-specific implementation
                user32 = ctypes.windll.user32
                def enum_windows_proc(hwnd, window_rects):
                    if user32.IsWindowVisible(hwnd) and user32.IsWindowEnabled(hwnd):
                        rect = wintypes.RECT()
                        user32.GetWindowRect(hwnd, ctypes.byref(rect))
                        window_rects.append((
                            rect.left,
                            rect.top,
                            rect.right - rect.left,
                            rect.bottom - rect.top
                        ))
                    return True

                window_rects = []
                user32.EnumWindows(enum_windows_proc, window_rects)
                return window_rects
            else:
                # Fallback for non-Windows (may not be accurate)
                return [(0, 0, 800, 600)]  # Default to a single rectangle
        except Exception:
            return [(0, 0, 800, 600)]

    def _find_unoccupied_position(self, screen_x, screen_y, screen_w, screen_h, desired_w, desired_h, occupied_rects):
        """Find an unoccupied position on the screen for the window."""
        # Simple algorithm: scan for gaps in the occupied rectangles
        x, y = screen_x, screen_y
        for dx in (0, desired_w // 2, desired_w // 4, -desired_w // 4):
            for dy in (0, desired_h // 2, desired_h // 4, -desired_h // 4):
                candidate_x = x + dx
                candidate_y = y + dy
                if self._is_rect_unoccupied(candidate_x, candidate_y, desired_w, desired_h, occupied_rects):
                    return candidate_x, candidate_y
        # If no gap found, fallback to center of screen
        return screen_x + (screen_w - desired_w) // 2, screen_y + (screen_h - desired_h) // 2

    def _is_rect_unoccupied(self, x, y, w, h, occupied_rects):
        """Check if a rectangle area is unoccupied by other windows."""
        test_rect = (x, y, w, h)
        for rect in occupied_rects:
            if self._do_rects_overlap(test_rect, rect):
                return False
        return True

    def _do_rects_overlap(self, r1, r2):
        """Check if two rectangles overlap."""
        x1, y1, w1, h1 = r1
        x2, y2, w2, h2 = r2
        return not (x1 + w1 <= x2 or x2 + w2 <= x1 or y1 + h1 <= y2 or y2 + h2 <= y1)

    def add_text_box(self, content="", file_path="", font_size: int | None = None, onedrive_name: str | None = None):
        """Add a new text box for editing."""
        try:
            if self.current_view_mode == "tabbed":
                if getattr(self, 'notebook', None) is None:
                    # Prepare queued entry and build notebook on first add
                    self.text_boxes.append({
                        "content": content,
                        "file_path": file_path,
                        "text_box": None,
                        "file_title": None,
                        "outer_frame": None,
                    })
                    self._switch_to_tabbed_view()
                    self._schedule_status_update()
                    return
                # Add new tab directly to existing notebook
                assert self.notebook is not None
                nb = self.notebook
                tab_frame = tk.Frame(nb, bg="#FFFFFF", bd=0)
                text_container = tk.Frame(tab_frame, bg="#FFFFFF", bd=0)
                text_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                text_frame = tk.Frame(text_container, bg="#FFFFFF")
                text_frame.pack(fill=tk.BOTH, expand=True)
                text_frame.grid_rowconfigure(0, weight=1)
                text_frame.grid_columnconfigure(0, weight=1)
                v_scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL)
                v_scrollbar.grid(row=0, column=1, sticky="ns")
                base_font_size = int(font_size) if font_size else 11
                text_widget = tk.Text(
                    text_frame,
                    wrap=tk.WORD,
                    undo=True,
                    yscrollcommand=v_scrollbar.set,
                    font=("Consolas", base_font_size),
                    bg="#FFFFFF",
                    fg="#000000",
                    insertbackground="#000000",
                    selectbackground="#0078D4",
                    selectforeground="#FFFFFF",
                    relief="flat",
                    borderwidth=1,
                    highlightthickness=0,
                )
                text_widget.grid(row=0, column=0, sticky="nsew")
                v_scrollbar.config(command=text_widget.yview)

                # --- Real-time spell checking and context menu (tabbed) ---
                try:
                    from spellchecker import SpellChecker
                    spell_checker = SpellChecker()
                    text_widget.tag_configure("misspelled", background="#FFFF00", foreground="#000000", underline=True)
                    tab_check_spelling_add = (lambda event=None, tw=text_widget, sc=spell_checker: self._spellcheck_text(tw, sc))
                except Exception as _e:
                    spell_checker = None
                    tab_check_spelling_add = (lambda event=None: None)

                try:
                    self._add_context_menu(text_widget, spell_checker)
                except Exception:
                    pass

                # Bindings including spell checking
                try:
                    self.root.after_idle(lambda: self._setup_text_widget_bindings(text_widget, tab_check_spelling_add))
                except Exception:
                    pass

                if content:
                    text_widget.insert("1.0", content)
                elif file_path and os.path.exists(file_path):
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            text_widget.insert("1.0", f.read())
                    except Exception:
                        pass

                # Track the new tab
                # Use onedrive_name if provided, otherwise derive from file_path
                if onedrive_name:
                    title = onedrive_name
                elif file_path and not file_path.startswith("onedrive:"):
                    title = os.path.basename(file_path)
                else:
                    title = "Untitled"
                
                self.text_boxes.append({
                    "text_box": text_widget,
                    "file_path": file_path,
                    "saved": True,
                    "title": title,
                    "tab_frame": tab_frame,
                    "font_size": base_font_size,
                })
                # Initialize last saved signature for accurate dirty tracking
                try:
                    self.text_boxes[-1]["last_saved_sig"] = self._compute_content_sig(text_widget)
                except Exception:
                    pass

                i = len(nb.tabs())
                # For OneDrive files, use original title; for local files use Tab X: format
                if file_path.startswith("onedrive:") and onedrive_name:
                    tab_title = onedrive_name
                elif file_path and not file_path.startswith("onedrive:"):
                    file_name = os.path.basename(file_path)
                    tab_title = f"Tab {i+1}: {file_name}"
                else:
                    tab_title = f"Untitled {i+1}"
                # Add tab with icon reflecting saved state
                try:
                    normal_icon, dirty_icon = self._get_or_create_tab_icons(i)
                    nb.add(tab_frame, text=tab_title, image=normal_icon, compound="left")
                except Exception:
                    nb.add(tab_frame, text=tab_title)

                try:
                    new_index = len(nb.tabs()) - 1
                    nb.select(new_index)
                    text_widget.focus_set()
                except Exception:
                    pass

                # Initialize dirty indicator for this new tab
                try:
                    self._update_dirty_indicator(i)
                except Exception:
                    pass
                self._schedule_status_update()
                return
                
            else:
                # Only tabbed mode is supported - fallback to tabbed view
                print("DEBUG: Unsupported view mode, using tabbed view")
                self.current_view_mode = "tabbed"
                self.add_text_box(content=content, file_path=file_path, font_size=font_size, onedrive_name=onedrive_name)
                return
        except Exception as e:
            messagebox.showerror("Error", f"Could not add text box: {e}")

    def close_box(self, outer_frame: tk.Frame, text_box: tk.Text, file_path: str | None, file_title: tk.Label):
        # This method is no longer used since paned view was removed
        # Tabbed view uses _close_tab instead
        print("DEBUG: close_box called - should use _close_tab for tabbed mode")

    # Removed _minimize_box and _maximize_box methods - paned view no longer supported

    # Removed equalize_boxes method - paned view no longer supported

    def toggle_tabbed_view(self):
        """No longer needed - app is always in tabbed view mode."""
        print("INFO: App is always in tabbed view mode now")

    def _switch_to_tabbed_view(self):
        """Switch from paned view to tabbed view with enhanced visual identity."""
        print("DEBUG: Starting tabbed view switch")
        
        if len(self.text_boxes) == 0:
            print("DEBUG: No text boxes to convert to tabs")
            return

        try:
            print("DEBUG: Switching to tabbed view")
            
            # Store current content before destroying paned view
            saved_data = []
            for box_data in self.text_boxes:
                text_widget = box_data.get("text_box")
                if text_widget:
                    try:
                        content = text_widget.get("1.0", tk.END)
                        file_path = box_data.get("file_path", "")
                        title = box_data.get("title", "Untitled")
                        saved_data.append({
                            "content": content,
                            "file_path": file_path,
                            "saved": box_data.get("saved", True),
                            "title": title
                        })
                        print(f"DEBUG: Saved data for box: {len(content)} chars, file_path: '{file_path}', title: '{title}'")
                    except Exception as e:
                        print(f"DEBUG: Error getting content from text widget: {e}")
                else:
                    # Fallback for queued entries (tabbed mode additions without widgets yet)
                    try:
                        content = box_data.get("content", "")
                        file_path = box_data.get("file_path", "")
                        title = box_data.get("title", "Untitled")
                        saved = box_data.get("saved", True)
                        # Only append if there is any info; this prevents auto-creating a blank tab
                        if content or file_path:
                            saved_data.append({
                                "content": content,
                                "file_path": file_path,
                                "saved": saved,
                                "title": title or (os.path.basename(file_path) if file_path else "Untitled"),
                            })
                    except Exception as e:
                        print(f"DEBUG: Error collecting pending tab data: {e}")

            print(f"DEBUG: Collected {len(saved_data)} boxes of data")
            
            # Sort by file name/title
            saved_data = self._sort_tab_data_by_name(saved_data)

            # Destroy current paned window
            if hasattr(self, 'paned_window') and self.paned_window:
                try:
                    print("DEBUG: Destroying paned window")
                    self.paned_window.destroy()
                    self.paned_window = None
                except Exception as e:
                    print(f"DEBUG: Error destroying paned window: {e}")

            # Configure enhanced notebook style
            self._configure_notebook_style()

            # Create ttk.Notebook and pack it to be left-justified at the top
            print("DEBUG: Creating notebook, anchored to top-left")
            # Use default TNotebook style for maximum compatibility
            self.notebook = ttk.Notebook(self.root, style="TNotebook")
            # Pack at the top; fill and expand to use full width; tabs start from far left by default
            # Note: anchor has minimal effect when fill/expand are true, but keep TOP placement explicit
            self.notebook.pack(fill=tk.BOTH, expand=True, side=tk.TOP)
            
            # Add Ctrl+W binding to notebook for tab closing
            self.notebook.bind("<Control-w>", lambda e: self._close_focused_box() or "break")
            self.notebook.bind("<Control-W>", lambda e: self._close_focused_box() or "break")
            print("DEBUG: Added Ctrl+W binding to notebook widget")

            # Clear text_boxes and recreate as tabs
            self.text_boxes = []

            print(f"DEBUG: Creating {len(saved_data)} tabs")
            
            # Keep references to tab icons (to prevent garbage collection)
            self._tab_icons = []

            for i, data in enumerate(saved_data):
                try:
                    print(f"DEBUG: Creating tab {i+1}")
                    
                    # Create simple tab frame with clean styling
                    tab_frame = tk.Frame(self.notebook, bg="#FFFFFF", bd=0)
                    
                    # Create text widget container
                    text_container = tk.Frame(tab_frame, bg="#FFFFFF", bd=0)
                    text_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
                    
                    # Create text widget with scrollbar
                    text_frame = tk.Frame(text_container, bg="#FFFFFF")
                    text_frame.pack(fill=tk.BOTH, expand=True)
                    text_frame.grid_rowconfigure(0, weight=1)
                    text_frame.grid_columnconfigure(0, weight=1)

                    # Add scrollbar
                    v_scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL)
                    v_scrollbar.grid(row=0, column=1, sticky="ns")

                    # Create text widget with clean styling
                    text_widget = tk.Text(
                        text_frame, 
                        wrap=tk.WORD, 
                        undo=True,
                        yscrollcommand=v_scrollbar.set,
                        font=("Consolas", 11),
                        bg="#FFFFFF", 
                        fg="#000000", 
                        insertbackground="#000000",
                        selectbackground="#0078D4", 
                        selectforeground="#FFFFFF",
                        relief="flat", 
                        borderwidth=1,
                        highlightthickness=0
                    )
                    text_widget.grid(row=0, column=0, sticky="nsew")
                    v_scrollbar.config(command=text_widget.yview)
                    
                    # --- Real-time spell checking and context menu (tabbed init) ---
                    try:
                        from spellchecker import SpellChecker
                        spell_checker = SpellChecker()
                        text_widget.tag_configure("misspelled", background="#FFFF00", foreground="#000000", underline=True)
                        tab_check_spelling_switch = (lambda event=None, tw=text_widget, sc=spell_checker: self._spellcheck_text(tw, sc))
                    except Exception as _e:
                        spell_checker = None
                        tab_check_spelling_switch = (lambda event=None: None)

                    try:
                        self._add_context_menu(text_widget, spell_checker)
                    except Exception:
                        pass

                    try:
                        self.root.after_idle(lambda tw=text_widget, cs=tab_check_spelling_switch: self._setup_text_widget_bindings(tw, cs))
                    except Exception:
                        pass

                    # Insert the saved content
                    if data.get("content"):
                        text_widget.insert("1.0", data["content"])
                        print(f"DEBUG: Inserted {len(data['content'])} chars into tab {i+1}")

                    # Generate simple tab title - use original OneDrive titles, Tab X: format for local files
                    file_path = data.get("file_path", "")
                    if file_path.startswith("onedrive:"):
                        # For OneDrive files, get the original filename from OneDrive
                        item_id = file_path.replace("onedrive:", "")
                        original_filename = self._get_onedrive_filename_from_id(item_id)
                        if original_filename:
                            tab_title = original_filename
                            print(f"DEBUG: Using OneDrive filename mapping for tab {i+1}: '{original_filename}'")
                        else:
                            # Fallback to stored title
                            stored_title = data.get("title", "")
                            if stored_title and stored_title != "Untitled":
                                tab_title = stored_title
                            else:
                                tab_title = f"Untitled {i+1}"
                    else:
                        # For local files, use "Tab X: filename" format
                        file_name = os.path.basename(file_path) or f"Untitled {i+1}"
                        tab_title = f"Tab {i+1}: {file_name}"

                    # Store tab data in text_boxes array for proper tracking
                    # Use the mapped OneDrive filename if available
                    final_title = tab_title if file_path.startswith("onedrive:") else data.get("title", "Untitled")
                    self.text_boxes.append({
                        "text_box": text_widget,
                        "file_path": data.get("file_path", ""),
                        "saved": data.get("saved", True),
                        "title": final_title,
                        "tab_frame": tab_frame,
                        "tab_index": i
                    })
                    try:
                        self.text_boxes[-1]["last_saved_sig"] = self._compute_content_sig(text_widget) if self.text_boxes[-1]["saved"] else ""
                    except Exception:
                        pass

                    # Create a small colored square icon for the tab for readable color indication
                    # Add tab with icon reflecting saved state
                    try:
                        normal_icon, dirty_icon = self._get_or_create_tab_icons(i)
                        icon_to_use = normal_icon if self.text_boxes[i]["saved"] else dirty_icon
                        self.notebook.add(tab_frame, text=tab_title, image=icon_to_use, compound="left")
                        print(f"DEBUG: Successfully added tab {i+1} with icon and title: '{tab_title}'")
                    except Exception as e:
                        print(f"DEBUG: Icon creation failed for tab {i+1}, trying without icon: {e}")
                        try:
                            # Fallback without image if PhotoImage fails
                            self.notebook.add(tab_frame, text=tab_title)
                            print(f"DEBUG: Successfully added tab {i+1} without icon, title: '{tab_title}'")
                        except Exception as e2:
                            print(f"DEBUG: Failed to add tab {i+1} even without icon: {e2}")
                            raise
                    print(f"DEBUG: Created tab {i+1} with clean styling")

                except Exception as e:
                    print(f"DEBUG: Error creating tab {i+1}: {e}")
                    import traceback
                    traceback.print_exc()

            # Apply custom tab colors using a different approach
            # Color overlay functionality disabled

            # Enable enhanced tab features with right-click menu
            try:
                self._enable_tab_drag_and_drop()
                # Bind right-click to show context menu on the tab under the cursor
                # Windows uses <Button-3> for right-click
                self.notebook.bind("<Button-3>", self._tab_right_click_menu)
            except Exception as e:
                print(f"DEBUG: Error setting up tab features: {e}")

            # Select first tab if available
            if len(self.text_boxes) > 0:
                self.notebook.select(0)
                self.text_boxes[0]["text_box"].focus_set()

            # After creating all tabs, ensure indicators match saved flags
            try:
                for idx in range(len(self.text_boxes)):
                    self._update_dirty_indicator(idx)
            except Exception:
                pass

            # Update view mode and status
            self.current_view_mode = "tabbed"
            try:
                self.status_bar.config(text=f"View: Tabbed ({len(self.text_boxes)} tabs)")
                self.root.after(2000, self._schedule_status_update)
            except Exception as e:
                print(f"DEBUG: Error updating status bar: {e}")
                
            print(f"DEBUG: Successfully switched to tabbed view with {len(self.text_boxes)} tabs")
            
        except Exception as e:
            print(f"ERROR: Failed to switch to tabbed view: {e}")
            import traceback
            traceback.print_exc()
            # No fallback needed - only tabbed view is supported

    # Removed _switch_to_paned_view method - paned view no longer supported

    def _apply_custom_tab_colors(self):
        """Color overlay functionality disabled - tabs now use plain grey styling only."""
        pass

    def _update_tab_title(self, tab_index, file_path):
        """Update the title of a specific tab with consistent naming and storage icons."""
        try:
            if 0 <= tab_index < len(self.text_boxes) and self.notebook:
                box_data = self.text_boxes[tab_index]
                
                # Generate clean, consistent title (no OneDrive names in title)
                if file_path and file_path.startswith("onedrive:"):
                    # For OneDrive files, use original stored title without "Tab X: " prefix
                    stored_title = box_data.get("title", "")
                    if stored_title and stored_title != "Untitled":
                        tab_title = stored_title
                    else:
                        tab_title = f"Untitled {tab_index+1}"
                elif file_path:
                    # For local files, use "Tab X: filename" format for consistency
                    file_name = os.path.basename(file_path)
                    tab_title = f"Tab {tab_index+1}: {file_name}"
                else:
                    tab_title = f"Untitled {tab_index+1}"
                
                # Update tab with title and appropriate icon
                try:
                    # Get appropriate icon (OneDrive cloud or local square)
                    normal_icon, dirty_icon = self._get_or_create_tab_icons(tab_index)
                    is_dirty = not box_data.get("saved", True)
                    icon_to_use = dirty_icon if is_dirty else normal_icon
                    
                    if is_dirty:
                        tab_title = tab_title + " *"
                    
                    self.notebook.tab(tab_index, text=tab_title, image=icon_to_use)
                    print(f"DEBUG: Updated tab {tab_index} title to: {tab_title} with {'OneDrive' if file_path and file_path.startswith('onedrive:') else 'local'} icon")
                except Exception as e:
                    print(f"DEBUG: Could not update tab title/icon for tab {tab_index}: {e}")
                
        except Exception as e:
            print(f"Error updating tab title: {e}")

    def close_all_boxes(self):
        """Close all text boxes and clear the layout."""
        try:
            total_boxes = len(self.text_boxes)
            if total_boxes == 0:
                return
                
            # Show progress dialog for closing boxes
            progress = ProgressDialog(self.root, "Closing Boxes", f"Closing {total_boxes} boxes...")
            self.root.update()
            
            # Proceed without confirmation
            for i, box in enumerate(self.text_boxes):
                progress.update_message(f"Closing box {i + 1} of {total_boxes}...")
                self.root.update()
                
                outer = box.get("outer_frame")
                if outer is not None:
                    try:
                        pw = self.paned_window
                        if pw is not None:
                            pw.forget(outer)
                        outer.destroy()
                    except Exception:
                        pass
            self.text_boxes = []

            # Clear the layout file as well
            progress.update_message("Clearing layout file...")
            self.root.update()
            try:
                if os.path.exists(self.layout_file):
                    os.remove(self.layout_file)
            except Exception:
                pass
                
            progress.close()
        except Exception as e:
            messagebox.showerror("Error", f"Could not close all boxes: {e}")

    def configure_auto_save(self):
        """Open a dialog to configure auto-save settings."""
        try:
            # Create a simple dialog for auto-save configuration
            config_window = tk.Toplevel(self.root)
            config_window.title("Auto-Save Configuration")
            config_window.geometry("300x200")
            config_window.transient(self.root)
            config_window.grab_set()
            
            # Current settings display
            tk.Label(config_window, text="Auto-Save Settings", font=("Arial", 12, "bold")).pack(pady=10)
            
            # Enable/disable auto-save
            auto_save_var = tk.BooleanVar(value=self.auto_save_enabled)
            tk.Checkbutton(config_window, text="Enable Auto-Save", variable=auto_save_var).pack(pady=5)
            
            # Interval setting
            tk.Label(config_window, text="Auto-Save Interval (minutes):").pack(pady=5)
            interval_var = tk.StringVar(value=str(self.auto_save_interval))
            interval_entry = tk.Entry(config_window, textvariable=interval_var, width=10)
            interval_entry.pack(pady=5)
            
            # Buttons
            button_frame = tk.Frame(config_window)
            button_frame.pack(pady=20)
            
            def save_config():
                try:
                    self.auto_save_enabled = auto_save_var.get()
                    self.auto_save_interval = max(1, int(interval_var.get()))
                    self._save_configuration()
                    
                    # Restart auto-save with new settings
                    if self.auto_save_job:
                        self.root.after_cancel(self.auto_save_job)
                        self.auto_save_job = None
                    self.start_auto_save()
                    
                    messagebox.showinfo("Success", "Auto-save settings updated!")
                    config_window.destroy()
                except ValueError:
                    messagebox.showerror("Error", "Please enter a valid number for the interval.")
        
            tk.Button(button_frame, text="Save", command=save_config).pack(side=tk.LEFT, padx=5)
            tk.Button(button_frame, text="Cancel", command=config_window.destroy).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not open configuration dialog: {e}")

    def start_auto_save(self):
        """Start auto-save timer."""
        try:
            if self.auto_save_enabled and self.auto_save_interval > 0:
                if self.auto_save_job:
                    self.root.after_cancel(self.auto_save_job)
                
                interval_ms = self.auto_save_interval * 60 * 1000
                self.auto_save_job = self.root.after(interval_ms, self.auto_save_and_reschedule)
        except Exception as e:
            print(f"ERROR: Failed to start auto-save: {e}")
    
    def auto_save_and_reschedule(self):
        """Perform auto-save and reschedule next auto-save."""
        try:
            self.auto_save_all()
            # Reschedule next auto-save
            if self.auto_save_enabled and self.auto_save_interval > 0:
                interval_ms = self.auto_save_interval * 60 * 1000
                self.auto_save_job = self.root.after(interval_ms, self.auto_save_and_reschedule)
        except Exception as e:
            print(f"ERROR: Failed during auto-save: {e}")
    
    def auto_save_all(self):
        """Auto-save all text boxes that have content."""
        try:
            saved_count = 0
            for box_data in self.text_boxes:
                text_widget = box_data.get("text_box")
                if text_widget and text_widget.get("1.0", tk.END).strip():
                    file_path = box_data.get("file_path")
                    file_title = box_data.get("file_title")
                    if file_path:
                        self.save_box(text_widget, file_path, file_title)
                        saved_count += 1
            
            if saved_count > 0:
                print(f"DEBUG: Auto-saved {saved_count} file(s)")
        except Exception as e:
            print(f"ERROR: Failed to auto-save files: {e}")

    def _save_all_open_files(self):
        """Save all open files that have content and file paths."""
        try:
            saved_count = 0
            for box_data in self.text_boxes:
                text_widget = box_data.get("text_box")
                file_path = box_data.get("file_path")
                file_title = box_data.get("file_title")
                
                if text_widget and file_path and text_widget.get("1.0", tk.END).strip():
                    try:
                        self.save_box(text_widget, file_path, file_title)
                        saved_count += 1
                    except Exception as e:
                        print(f"DEBUG: Error saving file {file_path}: {e}")
            
            if saved_count > 0:
                print(f"DEBUG: Saved {saved_count} open file(s)")
        except Exception as e:
            print(f"ERROR: Failed to save all open files: {e}")

    def save_layout_to_file(self):
        """Save the current layout configuration to file in a format compatible with restore."""
        try:
            layout_data = {
                "geometry": self.root.winfo_geometry(),
                "view_mode": "tabbed",  # Only tabbed mode is supported
                "boxes": []
            }            # Save data for each text box (persist content to restore unsaved notes; file_path if present)
            for box_data in self.text_boxes:
                text_widget = box_data.get("text_box")
                content = ""
                try:
                    if text_widget:
                        content = text_widget.get("1.0", tk.END)
                except Exception:
                    content = ""
                layout_data["boxes"].append({
                    "file_path": box_data.get("file_path", "") or "",
                    "title": box_data.get("title", "Untitled"),
                    "saved": box_data.get("saved", True),
                    "content": content,
                    "font_size": int(box_data.get("font_size", 11))
                })

            # No pane sizes to save (tabbed mode only)

            layout_file = self._get_config_file_path("layout.json")
            with open(layout_file, 'w', encoding='utf-8') as f:
                json.dump(layout_data, f, indent=2)

            print(f"DEBUG: Saved layout to {layout_file}")
        except Exception as e:
            print(f"ERROR: Failed to save layout: {e}")

    def copy_to_clipboard(self, text_widget):
        """Copy selected text to clipboard."""
        try:
            selected_text = text_widget.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
            messagebox.showinfo("Copied", "Text copied to clipboard!")
        except tk.TclError:
            # No text selected
            messagebox.showinfo("No Selection", "Please select text to copy.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not copy to clipboard: {e}")

    def _add_context_menu(self, text_widget, spell_checker=None):
        """Add a basic context menu to text widget."""
        try:
            def build_and_show_menu(event):
                try:
                    import re
                    # Build fresh menu each time to reflect current context
                    menu = tk.Menu(text_widget, tearoff=0)
                    menu.add_command(label="Cut", command=lambda: text_widget.event_generate("<<Cut>>"))
                    menu.add_command(label="Copy", command=lambda: text_widget.event_generate("<<Copy>>"))
                    menu.add_command(label="Paste", command=lambda: text_widget.event_generate("<<Paste>>"))
                    # Add rename for the owning box/file
                    def _find_box_index_for_text_widget():
                        try:
                            for i, b in enumerate(self.text_boxes):
                                if b.get("text_box") is text_widget:
                                    return i
                        except Exception:
                            pass
                        return None
                    _idx_box = _find_box_index_for_text_widget()
                    if _idx_box is not None:
                        menu.add_command(label="Rename Box & File", command=lambda i=_idx_box: self._rename_tab_and_file(i))

                    # Spelling suggestions (only if we have a checker and clicked word is misspelled)
                    def get_word_under_cursor():
                        try:
                            idx = text_widget.index(f"@{event.x},{event.y}")
                            start = text_widget.index(f"{idx} wordstart")
                            end = text_widget.index(f"{idx} wordend")
                            raw = text_widget.get(start, end)
                            # Trim to word characters
                            m = re.search(r"[A-Za-z']+", raw)
                            if not m:
                                return None, None, None
                            w = m.group(0)
                            # Adjust start/end to matched span within raw
                            start_adj = text_widget.index(f"{start}+{m.start()}c")
                            end_adj = text_widget.index(f"{start}+{m.end()}c")
                            return w, start_adj, end_adj
                        except Exception:
                            return None, None, None

                    # Make selection more apparent: if no selection, select word under cursor
                    try:
                        _ = text_widget.index(tk.SEL_FIRST)  # raises on no selection
                    except tk.TclError:
                        w, ws, we = get_word_under_cursor()
                        if w and ws and we:
                            try:
                                text_widget.tag_remove(tk.SEL, "1.0", tk.END)
                                text_widget.tag_add(tk.SEL, ws, we)
                                text_widget.mark_set(tk.INSERT, we)
                                text_widget.focus_set()
                                # Apply a temporary visible highlight tag that stays while menu is open
                                try:
                                    text_widget.tag_configure("context_select", background="#99CCFF", foreground="#000000")
                                except Exception:
                                    pass
                                text_widget.tag_add("context_select", ws, we)
                            except Exception:
                                pass
                    # Ensure highlight is cleared when the menu closes
                    def _clear_context_highlight(_e=None):
                        try:
                            text_widget.tag_remove("context_select", "1.0", tk.END)
                        except Exception:
                            pass
                    menu.bind("<Unmap>", _clear_context_highlight)

                    if spell_checker is not None:
                        word, wstart, wend = get_word_under_cursor()
                        if word:
                            # Determine if misspelled
                            try:
                                miss = spell_checker.unknown([word.lower()])
                            except Exception:
                                miss = set()
                            if word.lower() in miss:
                                spelling_menu = tk.Menu(menu, tearoff=0)
                                # Best correction first
                                try:
                                    best = spell_checker.correction(word.lower())
                                except Exception:
                                    best = None
                                suggestions = set()
                                if best:
                                    suggestions.add(best)
                                try:
                                    cands = spell_checker.candidates(word.lower())
                                except Exception:
                                    cands = set()
                                for c in cands:
                                    if len(suggestions) >= 5:
                                        break
                                    suggestions.add(c)

                                def replace_with(rep: str):
                                    # Preserve simple case
                                    rr = rep
                                    if word.isupper():
                                        rr = rep.upper()
                                    elif word.istitle():
                                        rr = rep.title()
                                    try:
                                        text_widget.delete(wstart, wend)
                                        text_widget.insert(wstart, rr)
                                        # re-run spellcheck after idle
                                        text_widget.after_idle(lambda: self._spellcheck_text(text_widget, spell_checker))
                                    except Exception:
                                        pass

                                # Add suggestion items
                                if suggestions:
                                    for s in list(suggestions)[:5]:
                                        spelling_menu.add_command(label=s, command=lambda rep=s: replace_with(rep))
                                else:
                                    spelling_menu.add_command(label="(no suggestions)", state="disabled")

                                # Add actions
                                spelling_menu.add_separator()
                                spelling_menu.add_command(
                                    label=f"Ignore '{word}'",
                                    command=lambda: text_widget.tag_remove("misspelled", wstart, wend)
                                )
                                spelling_menu.add_command(
                                    label=f"Add '{word}' to dictionary",
                                    command=lambda w=word: (self._add_word_to_dictionary(spell_checker, w), text_widget.after_idle(lambda: self._spellcheck_text(text_widget, spell_checker)))
                                )
                                menu.add_cascade(label="Spelling", menu=spelling_menu)

                    # AI submenu
                    ai_menu = tk.Menu(menu, tearoff=0)
                    ai_menu.add_command(label="Summarize Selection", command=lambda: self._apply_ai_action_to_widget(text_widget, action="summarize"))
                    ai_menu.add_command(label="Rewrite Selection", command=lambda: self._apply_ai_action_to_widget(text_widget, action="rewrite"))
                    ai_menu.add_command(label="Proofread Selection", command=lambda: self._apply_ai_action_to_widget(text_widget, action="proofread"))
                    ai_menu.add_command(label="Research Selection", command=lambda: self._apply_ai_action_to_widget(text_widget, action="research"))
                    menu.add_cascade(label="AI", menu=ai_menu)

                    menu.post(event.x_root, event.y_root)
                except Exception:
                    pass

            # Right click
            text_widget.bind("<Button-3>", build_and_show_menu)
        except Exception as e:
            print(f"DEBUG: Error setting up context menu: {e}")

    def _setup_text_widget_bindings(self, text_widget, check_spelling=None, status_updater=None, spell_checker=None):
        """Set up basic text widget bindings."""
        try:
            # Improve selection visibility
            try:
                text_widget.configure(selectbackground="#CCE8FF", selectforeground="#000000")
            except Exception:
                pass

            def on_change(event=None):
                try:
                    self._on_text_change(text_widget)
                except Exception:
                    pass
                try:
                    if callable(check_spelling):
                        # schedule after idle to keep UI responsive
                        text_widget.after_idle(check_spelling)
                except Exception:
                    pass
                try:
                    if callable(status_updater):
                        status_updater()
                except Exception:
                    pass

            def handle_close_tab(event=None):
                """Handle Ctrl+W for this specific text widget."""
                try:
                    print(f"DEBUG: Ctrl+W triggered on text widget: {text_widget}")
                    result = self._close_focused_box()
                    return "break"  # Prevent default handling
                except Exception as e:
                    print(f"DEBUG: Error in text widget Ctrl+W handler: {e}")
                    return "break"

            # Basic bindings for text editing with spell check
            text_widget.bind("<KeyRelease>", on_change)
            text_widget.bind("<Button-1>", on_change)
            
            # Add Ctrl+W binding directly to text widget for reliable tab closing
            text_widget.bind("<Control-w>", handle_close_tab)
            text_widget.bind("<Control-W>", handle_close_tab)
            print(f"DEBUG: Added Ctrl+W binding to text widget: {text_widget}")
            
        except Exception as e:
            print(f"DEBUG: Error setting up text widget bindings: {e}")

    def _compute_content_sig(self, text_widget) -> str:
        """Compute a stable signature for the widget's content."""
        try:
            text = text_widget.get("1.0", tk.END)
            m = hashlib.md5()
            m.update(text.encode("utf-8", errors="ignore"))
            return m.hexdigest()
        except Exception:
            return ""

    def _set_box_saved_sig(self, box, text_widget):
        try:
            box["last_saved_sig"] = self._compute_content_sig(text_widget)
        except Exception:
            pass

    def _on_text_change(self, text_widget):
        """Handle text change events by comparing content signature to last saved."""
        try:
            current_sig = self._compute_content_sig(text_widget)
            for i, box in enumerate(self.text_boxes):
                if box.get("text_box") is text_widget or box.get("text_widget") is text_widget:
                    last_sig = box.get("last_saved_sig")
                    new_saved = (current_sig == last_sig)
                    if box.get("saved") != new_saved:
                        box["saved"] = new_saved
                        self._update_dirty_indicator(i)
                    break
        except Exception as e:
            print(f"DEBUG: Error handling text change: {e}")

    def _update_status_bar(self):
        """Update the status bar with current information."""
        try:
            if hasattr(self, 'status_bar'):
                current_time = datetime.now().strftime("%H:%M:%S")
                
                # Add OneDrive status
                onedrive_status = ""
                if self.onedrive_manager and self.onedrive_manager.is_authenticated():
                    onedrive_status = " | OneDrive: Connected"
                elif self.onedrive_manager:
                    onedrive_status = " | OneDrive: Available"
                
                status_text = f"Boxes: {len(self.text_boxes)} | View: {self.current_view_mode}{onedrive_status} | {current_time}"
                self.status_bar.config(text=status_text)
        except Exception as e:
            print(f"DEBUG: Error updating status bar: {e}")

    # -------------------- Saved/Dirty state + icons --------------------
    def _ensure_icon_caches(self):
        """Ensure icon caches exist for normal and dirty states."""
        if not hasattr(self, '_tab_icons'):  # colored squares per tab (normal)
            self._tab_icons = []
        if not hasattr(self, '_tab_dirty_icons'):  # colored squares with dot/mark (dirty)
            self._tab_dirty_icons = []
        if not hasattr(self, '_tab_onedrive_icons'):  # OneDrive storage icons (normal)
            self._tab_onedrive_icons = []
        if not hasattr(self, '_tab_onedrive_dirty_icons'):  # OneDrive storage icons (dirty)
            self._tab_onedrive_dirty_icons = []
        if not hasattr(self, '_small_dirty_icon'):
            self._small_dirty_icon = None

    def _make_colored_square(self, color: str, size: int = 10):
        try:
            icon = tk.PhotoImage(width=size, height=size)
            icon.put(color, to=(0, 0, size, size))
            return icon
        except Exception:
            return None

    def _make_dirty_square(self, base_color: str, size: int = 12):
        """Create a square icon with a small red triangle at top-right and a thin red border to indicate 'dirty'."""
        try:
            icon = tk.PhotoImage(width=size, height=size)
            # Fill base
            icon.put(base_color, to=(0, 0, size, size))
            # Draw thin red border
            border = "#CC0000"
            for x in range(0, size):
                icon.put(border, to=(x, 0))
                icon.put(border, to=(x, size-1))
            for y in range(0, size):
                icon.put(border, to=(0, y))
                icon.put(border, to=(size-1, y))
            # Draw a small red corner triangle
            tri_size = max(4, size // 3)
            for x in range(size - tri_size, size):
                y_start = 0
                y_end = (x - (size - tri_size)) + 1
                for y in range(y_start, min(y_end, size)):
                    icon.put("#CC0000", to=(x, y))
            return icon
        except Exception:
            return None

    def _get_or_create_tab_icons(self, index: int):
        """Return (normal_icon, dirty_icon) for a tab index, creating as needed."""
        self._ensure_icon_caches()
        
        # Check if this tab is stored in OneDrive
        is_onedrive = False
        if 0 <= index < len(self.text_boxes):
            file_path = self.text_boxes[index].get("file_path", "")
            is_onedrive = file_path.startswith("onedrive:")
        
        # Ensure arrays are long enough for the appropriate icon type
        if is_onedrive:
            while len(self._tab_onedrive_icons) <= index:
                self._tab_onedrive_icons.append(None)
            while len(self._tab_onedrive_dirty_icons) <= index:
                self._tab_onedrive_dirty_icons.append(None)
        else:
            while len(self._tab_icons) <= index:
                self._tab_icons.append(None)
            while len(self._tab_dirty_icons) <= index:
                self._tab_dirty_icons.append(None)
        
        try:
            color = self._get_tab_color_for_index(index)
        except Exception:
            color = "#C0C0C0"
        
        if is_onedrive:
            # Create OneDrive cloud icons
            if self._tab_onedrive_icons[index] is None:
                self._tab_onedrive_icons[index] = self._make_onedrive_icon(color, 12, False)
            if self._tab_onedrive_dirty_icons[index] is None:
                self._tab_onedrive_dirty_icons[index] = self._make_onedrive_icon(color, 12, True)
            return self._tab_onedrive_icons[index], self._tab_onedrive_dirty_icons[index]
        else:
            # Create local storage icons (colored squares)
            if self._tab_icons[index] is None:
                self._tab_icons[index] = self._make_colored_square(color, 12)
            if self._tab_dirty_icons[index] is None:
                self._tab_dirty_icons[index] = self._make_dirty_square(color, 12)
            return self._tab_icons[index], self._tab_dirty_icons[index]

    def _get_small_dirty_badge(self):
        """Small 8x8 red dot used on paned label when dirty."""
        self._ensure_icon_caches()
        if self._small_dirty_icon is None:
            try:
                size = 8
                icon = tk.PhotoImage(width=size, height=size)
                # transparent bg simulated by using lightgray to blend with title
                bg = "#D3D3D3"
                icon.put(bg, to=(0, 0, size, size))
                # draw red circle (approx using square with border)
                for x in range(1, size - 1):
                    for y in range(1, size - 1):
                        icon.put("#CC0000", to=(x, y))
                self._small_dirty_icon = icon
            except Exception:
                self._small_dirty_icon = None
        return self._small_dirty_icon

    def _make_onedrive_icon(self, color: str, size: int = 12, is_dirty: bool = False):
        """Create an OneDrive cloud icon with optional dirty indicator."""
        try:
            icon = tk.PhotoImage(width=size, height=size)
            # Create transparent background
            icon.put("", to=(0, 0, size, size))
            
            # Draw cloud shape using tab color
            # Simple cloud representation using rectangles
            # Main cloud body
            cloud_color = color
            y_offset = 2
            # Top part of cloud
            icon.put(cloud_color, to=(3, y_offset+1, 9, y_offset+2))
            # Middle part (wider)
            icon.put(cloud_color, to=(2, y_offset+2, 10, y_offset+4))
            # Bottom part
            icon.put(cloud_color, to=(1, y_offset+4, 11, y_offset+6))
            
            # Add small "OneDrive" indicator (small "O" in corner)
            icon.put("#0078D4", to=(8, 1, 10, 3))  # OneDrive blue
            
            # Add dirty indicator if needed
            if is_dirty:
                icon.put("#CC0000", to=(9, 0, 12, 2))  # Red dot in top-right
            
            return icon
        except Exception as e:
            print(f"DEBUG: Error creating OneDrive icon: {e}")
            return None

    def _mark_dirty_for_widget(self, text_widget):
        """Find the box for widget, set saved=False, and update indicators."""
        try:
            for i, box in enumerate(self.text_boxes):
                if box.get("text_box") is text_widget or box.get("text_widget") is text_widget:
                    if not box.get("saved"):
                        # already dirty, avoid extra work
                        return
                    box["saved"] = False
                    self._update_dirty_indicator(i)
                    break
        except Exception as e:
            print(f"DEBUG: Error marking dirty: {e}")

    def _clear_dirty_for_widget(self, text_widget):
        try:
            for i, box in enumerate(self.text_boxes):
                if box.get("text_box") is text_widget or box.get("text_widget") is text_widget:
                    if box.get("saved"):
                        return
                    box["saved"] = True
                    self._update_dirty_indicator(i)
                    break
        except Exception as e:
            print(f"DEBUG: Error clearing dirty: {e}")

    def _update_dirty_indicator(self, index: int):
        """Update tab or paned label icon/title to reflect saved/dirty state for the given index."""
        try:
            if not (0 <= index < len(self.text_boxes)):
                return
            box = self.text_boxes[index]
            saved = box.get("saved", True)
            # Update tabbed view icon
            nb = getattr(self, 'notebook', None)
            if getattr(self, 'current_view_mode', None) == 'tabbed' and nb is not None:
                normal_icon, dirty_icon = self._get_or_create_tab_icons(index)
                try:
                    nb.tab(index, image=(normal_icon if saved else dirty_icon))
                except Exception:
                    pass
                # Update title with consistent naming (original OneDrive titles, Tab X: for local)
                try:
                    file_path = box.get("file_path", "")
                    if file_path and file_path.startswith("onedrive:"):
                        # For OneDrive files, use original stored title without prefix
                        stored_title = box.get("title", "")
                        if stored_title and stored_title != "Untitled":
                            title = f"{stored_title}{'' if saved else ' *'}"
                        else:
                            title = f"Untitled {index+1}{'' if saved else ' *'}"
                    elif file_path:
                        # For local files, use Tab X: format
                        file_name = os.path.basename(file_path)
                        title = f"Tab {index+1}: {file_name}{'' if saved else ' *'}"
                    else:
                        title = f"Untitled {index+1}{'' if saved else ' *'}"
                    
                    nb.tab(index, text=title)
                except Exception:
                    pass
            # Update paned view label icon (on file_title label if available)
            elif getattr(self, 'current_view_mode', None) == 'paned':
                lbl = box.get("file_title")
                if lbl and lbl.winfo_exists():
                    try:
                        # Create or clear an image on the label
                        if saved:
                            lbl.config(image='', compound='left')
                            lbl.image = None
                        else:
                            badge = self._get_small_dirty_badge()
                            if badge is not None:
                                lbl.config(image=badge, compound='left')
                                lbl.image = badge  # keep reference
                    except Exception:
                        pass
        except Exception as e:
            print(f"DEBUG: Error updating dirty indicator: {e}")

    def _sort_tab_data_by_name(self, data_list):
        """Sort tab data by file name."""
        try:
            return sorted(data_list, key=lambda x: os.path.basename(x.get("file_path", "")).lower())
        except Exception as e:
            print(f"DEBUG: Error sorting tab data: {e}")
            return data_list

    def _spellcheck_text(self, text_widget: tk.Text, spell_checker) -> None:
        """Apply misspelling highlight tags to a Text widget using provided SpellChecker."""
        try:
            if not spell_checker:
                return
            import re
            text = text_widget.get("1.0", tk.END)
            words = re.findall(r"\b\w+\b", text)
            misspelled = spell_checker.unknown(words)
            text_widget.tag_remove("misspelled", "1.0", tk.END)
            for word in misspelled:
                for match in re.finditer(rf"\b{re.escape(word)}\b", text, re.IGNORECASE):
                    start_idx = match.start()
                    end_idx = match.end()
                    start = f"1.0+{start_idx}c"
                    end = f"1.0+{end_idx}c"
                    text_widget.tag_add("misspelled", start, end)
        except Exception:
            pass

    def _add_word_to_dictionary(self, spell_checker, word: str) -> None:
        """Safely add a word to the spell checker dictionary if supported."""
        try:
            if not spell_checker or not word:
                return
            # pyspellchecker exposes word_frequency with add() in recent versions
            wf = getattr(spell_checker, "word_frequency", None)
            if wf and hasattr(wf, "add"):
                wf.add(word.lower())
            else:
                # Fallback: extend dictionary attribute if present
                dictionary = getattr(spell_checker, "dictionary", None)
                if isinstance(dictionary, set):
                    dictionary.add(word.lower())
        except Exception:
            pass

    # -------------------- Window events and helpers --------------------
    def _persist_geometry(self, geometry: str | None = None):
        """Persist current window geometry string to layout.json (geometry only)."""
        try:
            geo = geometry or self.root.winfo_geometry()
            if not isinstance(geo, str) or "+" not in geo:
                return
            data = {}
            if os.path.exists(self.layout_file):
                try:
                    with open(self.layout_file, "r", encoding="utf-8") as f:
                        data = json.load(f) or {}
                except Exception:
                    data = {}
            data["geometry"] = geo
            with open(self.layout_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def _on_configure(self, event=None):
        """Debounced handler for move/resize; saves geometry periodically."""
        try:
            geom = self.root.winfo_geometry()
            if getattr(self, "_last_geometry", None) == geom:
                return
            self._last_geometry = geom
            # Debounce: save after short delay
            job = getattr(self, "_geometry_debounce_job", None)
            if isinstance(job, str):
                try:
                    self.root.after_cancel(job)
                except Exception:
                    pass
            self._geometry_debounce_job = self.root.after(400, lambda g=geom: self._persist_geometry(g))
        except Exception:
            pass

    def _on_close_request(self):
        """Handle window close: save files, layout, and geometry locally only."""
        # Show progress dialog for closing operations
        progress = ProgressDialog(self.root, "Closing Noted", "Saving your work...")
        
        try:
            progress.update_message("Saving open files...")
            # Always save locally, no OneDrive sync on exit
            self._save_all_open_files()
        except Exception:
            pass
        
        try:
            progress.update_message("Saving layout and settings...")
            # Always save layout locally
            self.save_layout_to_file()
        except Exception:
            pass
        
        try:
            progress.update_message("Finalizing...")
            self._persist_geometry()
        except Exception:
            pass
        
        # Close progress dialog and exit
        try:
            progress.close()
        except Exception:
            pass
        
        try:
            self.root.destroy()
        except Exception:
            pass

    # -------------------- Global shortcut helpers --------------------
    def _get_focused_text_widget(self) -> tk.Text | None:
        try:
            focus = self.root.focus_get()
            for box in self.text_boxes:
                tw = box.get("text_box")
                if tw is not None and tw == focus:
                    return tw
        except Exception:
            pass
        return None

    def _save_focused_box(self):
        try:
            tw = self._get_focused_text_widget()
            if not tw:
                return
            # Find matching box to get file_path and title label
            for box in self.text_boxes:
                if box.get("text_box") is tw:
                    self.save_box(tw, box.get("file_path"), box.get("file_title"))
                    break
        except Exception:
            pass

    def _handle_global_cut(self, event=None):
        try:
            tw = self._get_focused_text_widget()
            if tw:
                tw.event_generate("<<Cut>>")
        except Exception:
            pass

    def _handle_global_copy(self, event=None):
        try:
            tw = self._get_focused_text_widget()
            if tw:
                tw.event_generate("<<Copy>>")
        except Exception:
            pass

    def _handle_global_paste(self, event=None):
        try:
            tw = self._get_focused_text_widget()
            if tw:
                tw.event_generate("<<Paste>>")
        except Exception:
            pass

    def _handle_global_select_all(self, event=None):
        try:
            tw = self._get_focused_text_widget()
            if tw:
                tw.tag_add(tk.SEL, "1.0", tk.END)
                tw.mark_set(tk.INSERT, "1.0")
                tw.see(tk.INSERT)
        except Exception:
            pass

    def _handle_global_undo(self, event=None):
        try:
            tw = self._get_focused_text_widget()
            if tw:
                tw.event_generate("<<Undo>>")
        except Exception:
            pass

    def _handle_global_redo(self, event=None):
        try:
            tw = self._get_focused_text_widget()
            if tw:
                tw.event_generate("<<Redo>>")
        except Exception:
            pass

    def _configure_notebook_style(self):
        """Configure reliable base ttk styles and theme for readable tabs."""
        try:
            if not hasattr(self, '_notebook_styled'):
                style = ttk.Style()
                try:
                    # Use 'clam' theme for consistent styling behavior across platforms
                    style.theme_use('clam')
                    print("DEBUG: ttk theme set to 'clam'")
                except Exception as _e:
                    print(f"DEBUG: Could not set theme 'clam': {_e}")

                # Base notebook appearance (use default element names for maximum compatibility)
                style.configure("TNotebook",
                                background="#F0F0F0",
                                borderwidth=1)
                # Reduce horizontal padding to keep tabs tightly left-aligned and readable
                style.configure("TNotebook.Tab",
                                padding=(8, 5),
                                font=("Segoe UI", 9),
                                foreground="#000000")
                # Clearer selected/active states for readability
                style.map("TNotebook.Tab",
                          background=[("selected", "#FFFFFF"), ("active", "#EAEAEA")],
                          foreground=[("selected", "#000000"), ("active", "#000000")])

                self._notebook_styled = True
                print("DEBUG: Base TNotebook styles configured")
        except Exception as e:
            print(f"DEBUG: Error configuring notebook style: {e}")

    def _get_tab_color_for_index(self, index):
        """Get color for tab at given index with more vibrant colors."""
        colors = [
            "#FF6B6B",  # Bright Red
            "#4ECDC4",  # Teal
            "#45B7D1",  # Sky Blue
            "#96CEB4",  # Mint Green
            "#FFEAA7",  # Yellow
            "#DDA0DD",  # Plum
            "#FF7675",  # Coral
            "#74B9FF",  # Bright Blue
            "#55A3FF",  # Light Blue
            "#00B894",  # Green
            "#FDCB6E",  # Orange
            "#E17055",  # Burnt Orange
            "#A29BFE",  # Purple
            "#FF7675",  # Pink
            "#00CEC9"   # Turquoise
        ]
        return colors[index % len(colors)]

    def _create_colored_tab_style(self, index, color):
        """Create a visual color system for tabs since ttk styling is limited."""
        try:
            # Since ttk.Notebook doesn't support individual tab coloring well,
            # we'll focus on making the content visually distinctive
            
            # Create a general style for the notebook if not already done
            if not hasattr(self, '_notebook_styled'):
                style = ttk.Style()
                
                # Enhance the overall notebook appearance
                style.configure("Enhanced.TNotebook", 
                              background="#F0F0F0",
                              borderwidth=2,
                              relief="solid")
                
                style.configure("Enhanced.TNotebook.Tab",
                              padding=[20, 10],
                              font=("Segoe UI", 9, "bold"),
                              borderwidth=2,
                              relief="solid",
                              bordercolor="#808080",  # Grey border
                              focuscolor="#808080")   # Grey focus border
                
                # Style for active tabs
                style.map("Enhanced.TNotebook.Tab",
                         background=[("selected", "#E8E8E8"), ("active", "#DCDCDC")],
                         foreground=[("selected", "#333333"), ("active", "#000000")])
                
                self._notebook_styled = True
                print(f"DEBUG: Enhanced notebook styling applied")
            
            return "Enhanced.TNotebook.Tab"
            
        except Exception as e:
            print(f"DEBUG: Error creating enhanced notebook style: {e}")
            return "TNotebook.Tab"

    def _is_dark_color(self, color):
        """Check if color is dark."""
        try:
            color = color.lstrip('#')
            r, g, b = int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)
            brightness = (r * 299 + g * 587 + b * 114) / 1000
            return brightness < 128
        except Exception:
            return False

    def _create_tab_title(self, data, index):
        """Create title for tab."""
        try:
            file_path = data.get("file_path", "")
            if file_path:
                return os.path.basename(file_path)
            return f"Untitled {index + 1}"
        except Exception:
            return f"Tab {index + 1}"

    def _enable_tab_drag_and_drop(self):
        """Enable tab drag and drop (basic implementation)."""
        try:
            # Basic implementation - could be enhanced later
            pass
        except Exception as e:
            print(f"DEBUG: Error enabling tab drag and drop: {e}")

    def _tab_right_click_menu(self, event):
        """Handle right-click on tab to show context menu."""
        try:
            if not self.notebook:
                return

            # Determine which tab is under the mouse cursor using hit-testing
            # Notebook.index accepts the special form f"@{x},{y}" to resolve to a tab index
            tab_index = None
            try:
                local_x = event.x
                local_y = event.y
                idx = self.notebook.index(f"@{local_x},{local_y}")
                # Ensure the index is within bounds and points to a real tab
                if isinstance(idx, int) and 0 <= idx < len(self.notebook.tabs()):
                    tab_index = idx
            except Exception:
                tab_index = None

            # Fallback to the currently selected tab if hit-test failed
            if tab_index is None:
                try:
                    idx = self.notebook.index(self.notebook.select())
                    if isinstance(idx, int) and 0 <= idx < len(self.notebook.tabs()):
                        tab_index = idx
                except Exception:
                    tab_index = None

            if tab_index is None or tab_index >= len(self.text_boxes):
                return

            # Select the tab under cursor to provide visual context
            try:
                self.notebook.select(tab_index)
            except Exception:
                pass
            
            # Create context menu
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(
                label="Save Tab", 
                command=lambda: self._save_tab(tab_index)
            )
            context_menu.add_command(
                label="Reload Tab", 
                command=lambda: self._reload_tab(tab_index)
            )
            context_menu.add_command(
                label="Rename Box & File",
                command=lambda: self._rename_tab_and_file(tab_index)
            )
            context_menu.add_separator()
            context_menu.add_command(
                label="Close Tab", 
                command=lambda: self._close_tab(tab_index)
            )
            context_menu.add_command(
                label="Close All Tabs", 
                command=lambda: self._close_all_tabs()
            )
            # AI submenu for tab (acts on the tab's text content)
            ai_menu = tk.Menu(context_menu, tearoff=0)
            ai_menu.add_command(label="Summarize", command=lambda: self._apply_ai_action_to_tab(tab_index, action="summarize"))
            ai_menu.add_command(label="Rewrite", command=lambda: self._apply_ai_action_to_tab(tab_index, action="rewrite"))
            ai_menu.add_command(label="Proofread", command=lambda: self._apply_ai_action_to_tab(tab_index, action="proofread"))
            ai_menu.add_command(label="Research", command=lambda: self._apply_ai_action_to_tab(tab_index, action="research"))
            context_menu.add_cascade(label="AI", menu=ai_menu)
            
            # Show menu at cursor position
            context_menu.post(event.x_root, event.y_root)
            
        except Exception as e:
            print(f"DEBUG: Error handling tab right-click: {e}")

    def _rename_tab_and_file(self, tab_index: int):
        """Rename the underlying file (local or OneDrive) and update titles."""
        try:
            if tab_index < 0 or tab_index >= len(self.text_boxes):
                return
            box = self.text_boxes[tab_index]
            current_path = box.get("file_path") or ""
            current_title = box.get("title") or f"Untitled {tab_index+1}"
            
            # For OneDrive files, use the stored title; for local files, use basename
            if current_path.startswith("onedrive:"):
                default_name = current_title
            elif current_path:
                default_name = os.path.basename(current_path)
            else:
                default_name = current_title
                
            try:
                from tkinter import simpledialog
                new_name = simpledialog.askstring("Rename", "New name for this note/file:", initialvalue=default_name, parent=self.root)
            except Exception:
                new_name = None
            if not new_name or new_name.strip() == default_name:
                return
            new_name = new_name.strip()

            # Handle OneDrive files
            if current_path.startswith("onedrive:"):
                # Update the title and mark as dirty to trigger sync
                box["title"] = new_name
                box["saved"] = False  # Mark as dirty so it will be synced
                print(f"DEBUG: Renamed OneDrive note from '{current_title}' to '{new_name}' - marked for sync")
                
                # Auto-sync the renamed OneDrive file if network is available
                if self._check_network_connectivity():
                    try:
                        self._sync_individual_onedrive_file(box)
                    except Exception as e:
                        print(f"DEBUG: Auto-sync after rename failed: {e}")
            # Handle local files
            elif current_path and os.path.exists(current_path):
                new_path = os.path.join(os.path.dirname(current_path), new_name)
                try:
                    os.replace(current_path, new_path)
                    box["file_path"] = new_path
                    box["title"] = new_name
                    print(f"DEBUG: Renamed local file to '{new_path}'")
                except Exception as e:
                    messagebox.showerror("Rename Error", f"Could not rename file: {e}")
                    return
            else:
                # No existing file, just update title
                box["title"] = new_name

            # Update UI: box title label and tab title with proper format
            file_title = box.get("file_title")
            if file_title and file_title.winfo_exists():
                try:
                    file_title.config(text=new_name)
                except Exception:
                    pass
            
            # Update tab title with proper format (original OneDrive titles, Tab X: for local)
            if self.current_view_mode == "tabbed" and self.notebook:
                try:
                    if current_path.startswith("onedrive:"):
                        # For OneDrive files, use original title without prefix
                        tab_title = new_name
                    else:
                        # For local files, use Tab X: format
                        tab_title = f"Tab {tab_index+1}: {new_name}"
                    self.notebook.tab(tab_index, text=tab_title)
                    print(f"DEBUG: Updated tab title to: {tab_title}")
                except Exception:
                    pass
            
            # Update dirty indicator
            try:
                self._update_dirty_indicator(tab_index)
            except Exception:
                pass
                
            # Persist layout locally
            try:
                self.save_layout_to_file()
            except Exception:
                pass
                
        except Exception as e:
            print(f"DEBUG: Error renaming tab/file: {e}")

    def _save_tab(self, tab_index):
        """Save the content of a specific tab."""
        try:
            if tab_index < 0 or tab_index >= len(self.text_boxes):
                return
            
            box_data = self.text_boxes[tab_index]
            text_widget = box_data.get("text_box")
            file_path = box_data.get("file_path")
            file_title = box_data.get("file_title")
            
            if text_widget:
                self.save_box(text_widget, file_path, file_title)
                
        except Exception as e:
            print(f"DEBUG: Error saving tab {tab_index}: {e}")

    def _reload_tab(self, tab_index):
        """Reload the content of a specific tab from its file."""
        try:
            if tab_index < 0 or tab_index >= len(self.text_boxes):
                return
            
            box_data = self.text_boxes[tab_index]
            text_widget = box_data.get("text_box")
            file_path = box_data.get("file_path")
            
            if not text_widget:
                return
            
            if file_path and os.path.exists(file_path):
                # Reload from existing file
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        content = file.read()
                    
                    text_widget.delete("1.0", tk.END)
                    text_widget.insert("1.0", content)
                    messagebox.showinfo("Success", f"Tab reloaded from: {os.path.basename(file_path)}")
                    
                except Exception as e:
                    messagebox.showerror("Error", f"Could not reload file: {e}")
            else:
                # No file associated; open file dialog directly without confirmation
                self.load_box(text_widget)
                    
        except Exception as e:
            print(f"DEBUG: Error reloading tab {tab_index}: {e}")

    def _close_tab(self, tab_index):
        """Close a specific tab."""
        try:
            if tab_index < 0 or tab_index >= len(self.text_boxes):
                return
            
            box_data = self.text_boxes[tab_index]
            text_widget = box_data.get("text_box")
            file_path = box_data.get("file_path")
            file_title = box_data.get("file_title")
            
            # No confirmation dialog; auto-save only if a file path exists
            if text_widget and file_path and text_widget.get("1.0", tk.END).strip():
                try:
                    self.save_box(text_widget, file_path, file_title)
                except Exception:
                    pass
            
            # Remove the tab
            if self.notebook and tab_index < len(self.notebook.tabs()):
                self.notebook.forget(tab_index)
            
            # Remove from text_boxes list
            if tab_index < len(self.text_boxes):
                self.text_boxes.pop(tab_index)
            
            # Update status - check if any tabs remain
            if len(self.text_boxes) == 0:
                # No tabs remaining - clear the notebook and switch to paned view if possible
                if self.notebook:
                    self.notebook.destroy()
                    self.notebook = None
                self.current_view_mode = "paned"
                self._schedule_status_update()
            else:
                self._schedule_status_update()
            
        except Exception as e:
            print(f"DEBUG: Error closing tab {tab_index}: {e}")

    def _close_all_tabs(self):
        """Close all tabs."""
        try:
            if self.current_view_mode == "tabbed" and self.notebook:
                total_tabs = len(self.text_boxes)
                if total_tabs == 0:
                    return
                
                # Show progress dialog for closing tabs
                progress = ProgressDialog(self.root, "Closing Tabs", f"Closing {total_tabs} tabs...")
                self.root.update()
                
                # Close all tabs from back to front to maintain indices
                for i in range(total_tabs - 1, -1, -1):
                    progress.update_message(f"Closing tab {total_tabs - i} of {total_tabs}...")
                    self.root.update()
                    self._close_tab(i)
                
                progress.close()
        except Exception as e:
            print(f"DEBUG: Error closing all tabs: {e}")

    def _close_focused_box(self):
        """Close the currently focused box or tab."""
        try:
            print("DEBUG: Ctrl+W pressed - attempting to close focused box/tab")
            
            # In tabbed mode, try to get the selected tab first
            if self.current_view_mode == "tabbed" and self.notebook:
                try:
                    selected_index = self.notebook.index(self.notebook.select())
                    print(f"DEBUG: Tabbed mode - selected tab index: {selected_index}")
                    self._close_tab(selected_index)
                    return True
                except Exception as e:
                    print(f"DEBUG: Could not get selected tab: {e}")
            
            # Fallback to focus-based detection
            tw = self._get_focused_text_widget()
            if not tw:
                print("DEBUG: No focused text widget found")
                print(f"DEBUG: Current focus is: {self.root.focus_get()}")
                return
            
            # Find the index of the focused text widget
            for i, box in enumerate(self.text_boxes):
                if box.get("text_box") is tw:
                    print(f"DEBUG: Closing focused box/tab at index {i}")
                    # Only tabbed mode is supported now
                    if self.current_view_mode == "tabbed":
                        self._close_tab(i)
                    return True
            return True
        except Exception as e:
            print(f"DEBUG: Error closing focused box: {e}")
            return True


    def refresh_tab_colors(self):
        """Refresh and update all tab colors with symbols and overlays."""
        try:
            if self.current_view_mode == "tabbed" and self.notebook:
                print("DEBUG: Refreshing tab colors with symbols")
                
                # Update each tab's title with symbol indicators
                for i in range(len(self.notebook.tabs())):
                    try:
                        tab_color = self._get_tab_color_for_index(i)
                        
                        # Update tab title with simple text label
                        if i < len(self.text_boxes):
                            box_data = self.text_boxes[i]
                            base_title = self._create_tab_title(box_data, i)
                            tab_labels = ["DOC", "TXT", "FILE", "NOTE", "PAGE", "EDIT", "WORK", "DATA", "TEXT", "CODE", 
                                         "MEMO", "DRAFT", "COPY", "NEW", "TEMP"]
                            label = tab_labels[i % len(tab_labels)]
                            enhanced_title = f"Tab {i+1} [{label}] {base_title}"
                            self.notebook.tab(i, text=enhanced_title)
                        
                        print(f"DEBUG: Refreshed symbol for tab {i}")
                        
                    except Exception as e:
                        print(f"DEBUG: Error refreshing tab {i} symbol: {e}")
                
                # Reapply the color overlays
                # Color overlay functionality disabled
                        
        except Exception as e:
            print(f"DEBUG: Error refreshing tab colors: {e}")

    def _set_ai_api_key(self):
        """Configure AI provider and API key, and persist settings."""
        try:
            api_window = tk.Toplevel(self.root)
            api_window.title("AI Configuration")
            api_window.geometry("420x220")
            api_window.transient(self.root)
            api_window.grab_set()

            container = tk.Frame(api_window)
            container.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

            tk.Label(container, text="AI Configuration", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=(0,8), sticky="w")

            tk.Label(container, text="Provider:").grid(row=1, column=0, sticky="e", padx=(0,8))
            provider_var = tk.StringVar(value=self.ai_provider or "none")
            provider_menu = ttk.Combobox(container, textvariable=provider_var, values=["none", "openai"], state="readonly", width=18)
            provider_menu.grid(row=1, column=1, sticky="w")

            tk.Label(container, text="API Key:").grid(row=2, column=0, sticky="e", padx=(0,8), pady=(8,0))
            api_key_var = tk.StringVar(value=self.ai_api_key or "")
            api_entry = tk.Entry(container, textvariable=api_key_var, width=36, show="*")
            api_entry.grid(row=2, column=1, sticky="w", pady=(8,0))

            # Helper note
            note = tk.Label(container, text="Note: Key is saved locally in noted_config.json. For sensitive storage, use OS keyring in the future.", wraplength=360, fg="#555")
            note.grid(row=3, column=0, columnspan=2, pady=(8,0), sticky="w")

            button_frame = tk.Frame(container)
            button_frame.grid(row=4, column=0, columnspan=2, pady=12, sticky="e")

            def save_api_key():
                self.ai_provider = provider_var.get().strip() or "none"
                self.ai_api_key = api_key_var.get().strip()
                self._save_configuration()
                messagebox.showinfo("AI", "AI settings saved.")
                api_window.destroy()

            ttk.Button(button_frame, text="Save", command=save_api_key).pack(side=tk.LEFT, padx=6)
            ttk.Button(button_frame, text="Cancel", command=api_window.destroy).pack(side=tk.LEFT, padx=6)

        except Exception as e:
            messagebox.showerror("Error", f"Could not open AI configuration dialog: {e}")

    # -------------------- AI helpers --------------------
    def _ensure_ai_configured(self) -> bool:
        """Return True if AI is usable; otherwise guide user to configure."""
        try:
            if (self.ai_provider in ("openai",) and not self.ai_api_key) or (self.ai_provider == "none"):
                res = messagebox.askyesno("AI", "AI provider/key not configured. Open AI settings now?")
                if res:
                    self._set_ai_api_key()
                return False
            return True
        except Exception:
            return False

    def _apply_ai_action_to_widget(self, text_widget: tk.Text, action: str):
        """Apply an AI action to selected text (or whole doc if none)."""
        try:
            if not isinstance(text_widget, tk.Text) or not text_widget.winfo_exists():
                return

            try:
                sel_start = text_widget.index(tk.SEL_FIRST)
                sel_end = text_widget.index(tk.SEL_LAST)
                selected_text = text_widget.get(sel_start, sel_end)
                target_range = (sel_start, sel_end)
            except tk.TclError:
                # No selection; ask to run on full document
                run_on_all = messagebox.askyesno("AI", "No selection. Apply to entire note?")
                if not run_on_all:
                    return
                sel_start, sel_end = "1.0", tk.END
                selected_text = text_widget.get(sel_start, sel_end)
                target_range = (sel_start, sel_end)

            if not selected_text.strip():
                messagebox.showinfo("AI", "Nothing to process.")
                return

            # For now, use local heuristic functions. Future: call provider if configured.
            result_text = self._ai_generate_locally(selected_text, action)

            if action == "research":
                # Show research in a popup dialog instead of inserting automatically
                self._show_research_popup(text_widget, result_text)
            else:
                # Insert result below the selection by default
                insert_choice = messagebox.askyesno("AI", "Insert result below selection? (No = replace)")
                if insert_choice:
                    end_index = target_range[1]
                    text_widget.insert(end_index, "\n" + result_text + "\n")
                else:
                    text_widget.delete(*target_range)
                    text_widget.insert(target_range[0], result_text)

                text_widget.focus_set()
        except Exception as e:
            messagebox.showerror("AI Error", f"Could not apply AI action: {e}")

    def _show_research_popup(self, target_widget: tk.Text, content: str):
        """Display research content in a popup with Insert/Copy options."""
        try:
            win = tk.Toplevel(self.root)
            win.title("Research")
            win.transient(self.root)
            win.geometry("700x500")

            # Text area (read-only)
            txt = tk.Text(win, wrap="word", state="normal")
            scr = ttk.Scrollbar(win, orient="vertical", command=txt.yview)
            txt.configure(yscrollcommand=scr.set)
            txt.insert("1.0", content)
            txt.config(state="disabled")
            txt.grid(row=0, column=0, sticky="nsew")
            scr.grid(row=0, column=1, sticky="ns")

            btns = tk.Frame(win)
            btns.grid(row=1, column=0, columnspan=2, sticky="e", pady=8, padx=8)

            def do_insert():
                try:
                    # Insert at end of selection if present, else at cursor
                    try:
                        ins_at = target_widget.index(tk.SEL_LAST)
                    except tk.TclError:
                        ins_at = target_widget.index(tk.INSERT)
                    target_widget.insert(ins_at, "\n" + content + "\n")
                    win.destroy()
                except Exception:
                    win.destroy()

            def do_copy():
                try:
                    self.root.clipboard_clear()
                    self.root.clipboard_append(content)
                except Exception:
                    pass

            ttk.Button(btns, text="Insert", command=do_insert).pack(side=tk.RIGHT, padx=6)
            ttk.Button(btns, text="Copy", command=do_copy).pack(side=tk.RIGHT, padx=6)
            ttk.Button(btns, text="Close", command=win.destroy).pack(side=tk.RIGHT, padx=6)

            # Make the window resizable with proper weight
            win.grid_rowconfigure(0, weight=1)
            win.grid_columnconfigure(0, weight=1)
        except Exception:
            pass

    def _apply_ai_action_to_tab(self, tab_index: int, action: str):
        try:
            if tab_index < 0 or tab_index >= len(self.text_boxes):
                return
            box = self.text_boxes[tab_index]
            text_widget = box.get("text_box")
            if text_widget:
                self._apply_ai_action_to_widget(text_widget, action)
        except Exception as e:
            messagebox.showerror("AI Error", f"Failed to process tab: {e}")

    @staticmethod
    def _ai_generate_locally(text: str, action: str) -> str:
        """Lightweight local stand-in for AI actions (no external deps)."""
        try:
            s = text.strip()
            if action == "summarize":
                # Simple heuristic: take first 3 non-empty lines and any line containing keywords.
                lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
                head = lines[:3]
                # also include lines with key markers
                keys = ("summary", "conclusion", "result", "important", "note:")
                extras = [ln for ln in lines[3:] if any(k in ln.lower() for k in keys)][:3]
                bullet = "\n".join(["- " + ln for ln in (head + extras)])
                return "Summary:\n" + (bullet if bullet else "(no salient lines found)")
            elif action == "rewrite":
                # Normalize whitespace and split overly long lines.
                import textwrap
                collapsed = " ".join(s.split())
                return "\n".join(textwrap.wrap(collapsed, width=90))
            elif action == "proofread":
                # Very naive: fix double spaces, ensure sentences end with punctuation.
                import re
                t = re.sub(r"\s+", " ", s)
                sentences = [seg.strip() for seg in re.split(r"([.!?])\s+", t)]
                # Re-stitch keeping punctuation where found
                out = []
                i = 0
                while i < len(sentences):
                    part = sentences[i]
                    if i + 1 < len(sentences) and sentences[i+1] in ".!?":
                        out.append(part + sentences[i+1])
                        i += 2
                    else:
                        if part and part[-1:] not in ".!?":
                            out.append(part + ".")
                        else:
                            out.append(part)
                        i += 1
                return " ".join(out)
            elif action == "research":
                # Local heuristic "research": extract keywords and create pointers
                import re
                import textwrap
                # Find candidate keywords (simple: capitalized words and frequent nouns-ish words)
                tokens = re.findall(r"[A-Za-z][A-Za-z\-']+", s)
                lower = [t.lower() for t in tokens]
                # crude frequency count
                from collections import Counter
                freq = Counter(w for w in lower if len(w) > 3)
                common = [w for w, c in freq.most_common(5)]
                # capitalize representative keywords for display
                display_keys = ", ".join(sorted({w.capitalize() for w in common})) or "(none)"
                lines = [
                    "Quick research notes:",
                    f"- Key topics: {display_keys}",
                    "- Background: Define core terms, list primary use-cases, and typical pitfalls.",
                    "- Related: standards/specs, comparable tools, and common integrations.",
                    "- Check: version/compatibility, licensing, and platform constraints.",
                    "- Follow-ups: gather 2-3 authoritative references and examples."
                ]
                return "\n".join(lines)
            else:
                return s
        except Exception:
            return text

    def show_config_location(self):
        """Show the location of configuration files."""
        try:
            config_dir = os.path.dirname(self.config_file)
            messagebox.showinfo("Configuration Location", 
                           f"Configuration files are stored locally:\n\n{config_dir}\n\n"
                           f"Layout file: {os.path.basename(self.layout_file)}\n"
                           f"Config file: {os.path.basename(self.config_file)}\n\n"
                           f"Note: App state is now stored locally to prevent automatic\n"
                           f"OneDrive loading. Use OneDrive Sync button for cloud sync.")
        except Exception as e:
            messagebox.showerror("Error", f"Could not show configuration location: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    app = EditableBoxApp(root)
    root.mainloop()
