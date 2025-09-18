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

        # Box arrangement state tracking
        self.current_arrangement = "horizontal"  # "horizontal", "vertical"
        
        # View mode tracking - "paned" or "tabbed"
        self.current_view_mode = "paned"  # Start in paned mode, then switch to tabbed
        
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
            {"label": "Add Box", "cmd": self.add_text_box, "style": {"bg": "#006400", "fg": "white"}},  # dark green
            {"label": "Arrange Boxes", "cmd": lambda: self.cycle_box_arrangement(), "style": {"bg": "#87CEEB", "fg": "black"}},  # sky blue - TEST WITH LAMBDA
            {"label": "Tabbed View", "cmd": self.toggle_tabbed_view, "style": {"bg": "#9370DB", "fg": "white"}},  # medium purple
            {"label": "Open Files", "cmd": self.open_multiple_files, "style": {"bg": "#4169E1", "fg": "white"}},  # royal blue
            {"label": "Insert Date/Time", "cmd": self.insert_datetime, "style": {"bg": "#87CEEB", "fg": "black"}},  # sky blue
            {"label": "Equalize Boxes", "cmd": self.equalize_boxes, "style": {"bg": "#ADD8E6"}},  # light blue
            {"label": "Auto-Save Config", "cmd": self.configure_auto_save, "style": {"bg": "#DDA0DD"}},  # plum
            {"label": "AI Config", "cmd": self._set_ai_api_key, "style": {"bg": "#FFB6C1", "fg": "black"}},  # light pink
            {"label": "Sync OneDrive", "cmd": self.authenticate_onedrive, "style": {"bg": "#0078D4", "fg": "white"}},  # Microsoft blue
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

        # Paned window for boxes
        self.paned_window = tk.PanedWindow(self.root, orient=tk.VERTICAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True)

        # Mark initialized before restoring boxes (add_text_box requires this)
        self._initialized = True
        self._restore_boxes_from_layout()

        # Switch to tabbed mode after initialization
        self.root.after(100, self._initialize_tabbed_mode)

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
        """Get configuration file path, preferring OneDrive for cross-device sync."""
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
            
            # First try to load from OneDrive if authenticated
            if self.onedrive_manager and self.onedrive_manager.is_authenticated():
                print("DEBUG: OneDrive authenticated, loading notes from cloud...")
                try:
                    notes = self.onedrive_manager.list_notes()
                    if notes:
                        print(f"DEBUG: Found {len(notes)} notes in OneDrive")
                        for note_item in notes:
                            file_name = note_item.get("name", "")
                            item_id = note_item.get("id", "")
                            
                            if file_name and item_id:
                                note_data = self.onedrive_manager.get_note_content(item_id)
                                if note_data and isinstance(note_data, dict):
                                    content = note_data.get("content", "")
                                    # Use the file name (without .json) as the note title
                                    title = file_name.replace(".json", "") if file_name.endswith(".json") else file_name
                                    self.add_text_box(content=content, file_path=f"onedrive:{item_id}", onedrive_name=title)
                        
                        print(f"DEBUG: Successfully loaded {len(notes)} notes from OneDrive")
                        return  # Skip local layout loading
                    else:
                        print("DEBUG: No notes found in OneDrive, falling back to local layout")
                except Exception as e:
                    print(f"DEBUG: Failed to load from OneDrive: {e}")
                    print("DEBUG: Falling back to local layout")
            else:
                print("DEBUG: OneDrive not authenticated, loading from local layout")
            
            # Load from local layout file (fallback or default behavior)
            layout = None
            if os.path.exists(self.layout_file):
                try:
                    with open(self.layout_file, "r", encoding="utf-8") as file:
                        layout = json.load(file)
                except Exception:
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
                    for i, box in enumerate(boxes):
                        try:
                            content = box.get("content", "") if isinstance(box, dict) else ""
                            file_path = box.get("file_path") if isinstance(box, dict) else None
                            font_size = box.get("font_size") if isinstance(box, dict) else None
                            self.add_text_box(content=content, file_path=file_path or "", font_size=font_size)
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

        # TEST: Arrange boxes shortcut: Ctrl+Shift+A
        try:
            self.root.bind_all("<Control-Shift-A>", lambda e: self.cycle_box_arrangement())
            print("DEBUG: Added Ctrl+Shift+A shortcut for arrange boxes")
        except Exception as ex:
            print(f"DEBUG: Failed to bind Ctrl+Shift+A: {ex}")

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

    def _initialize_tabbed_mode(self):
        """Initialize the app in tabbed mode after all components are set up."""
        try:
            print("DEBUG: Initializing tabbed mode on startup")
            if self.current_view_mode == "paned":
                self.toggle_tabbed_view()
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
            add_bullet("Dual views: Paned (multi-box) and Tabbed (notebook-style)", "blue")
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
            add_bullet("Equalize and arrange boxes (paned view only)", "green")
            add_bullet("Tab ↔ Paned switching preserves your content", "orange")

            txt.config(state="disabled")
            txt.pack(side="left", fill="both", expand=True)
            scr.pack(side="right", fill="y")

            btns = tk.Frame(win, bg="#ffffff")
            btns.pack(fill="x", padx=16, pady=8)
            ttk.Button(btns, text="Close", command=win.destroy).pack(side="right")
        except Exception as e:
            messagebox.showerror("Error", f"Could not show about dialog: {e}")
    
    # OneDrive Integration Methods
    def authenticate_onedrive(self):
        """Initiate OneDrive authentication."""
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

        def auth_and_reload():
            """Background authentication thread"""
            try:
                flow = self.onedrive_manager.app.initiate_device_flow(scopes=self.onedrive_manager.SCOPES)
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
                    
                    # Show success and offer to load notes
                    user_info = self.onedrive_manager.get_user_info()
                    user_name = user_info.get("name", "Unknown") if user_info else "Unknown"
                    
                    def success_callback():
                        result = messagebox.askyesno("OneDrive Connected", 
                            f"Successfully connected to OneDrive as {user_name}!\n\nWould you like to load your notes from OneDrive now?")
                        if result:
                            self._load_notes_from_onedrive()
                    
                    self.root.after(0, success_callback)
                else:
                    self.root.after(0, lambda: messagebox.showerror("Authentication Failed", "Authentication failed or was cancelled."))
                    
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Authentication Error", f"Authentication error: {e}"))

        # Start authentication in background thread
        threading.Thread(target=auth_and_reload, daemon=True).start()

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

    def _load_notes_from_onedrive(self):
        """Load notes from OneDrive and populate the UI"""
        if not self.onedrive_manager or not self.onedrive_manager.is_authenticated():
            messagebox.showwarning("OneDrive", "Not authenticated with OneDrive. Please sync first.")
            return
        
        try:
            # Clear existing boxes first
            self._clear_all_boxes()
            
            notes = self.onedrive_manager.list_notes()
            if not notes:
                messagebox.showinfo("OneDrive", "No notes found in your OneDrive app folder. The app folder will be created when you save your first note.")
                self.add_text_box()  # Add empty box
                return
            
            # Load each note
            for note_item in notes:
                file_name = note_item.get("name", "")
                item_id = note_item.get("id", "")
                
                if file_name and item_id:
                    note_data = self.onedrive_manager.get_note_content(item_id)
                    if note_data and isinstance(note_data, dict):
                        content = note_data.get("content", "")
                        # Use the file name (without .json) as the note title
                        title = file_name.replace(".json", "") if file_name.endswith(".json") else file_name
                        self.add_text_box(content=content, file_path=f"onedrive:{item_id}", onedrive_name=title)
            
            messagebox.showinfo("OneDrive", f"Loaded {len(notes)} notes from OneDrive!")
            
        except Exception as e:
            messagebox.showerror("OneDrive Error", f"Failed to load notes from OneDrive: {e}")

    def _clear_all_boxes(self):
        """Clear all text boxes from the current view"""
        if self.current_view_mode == "tabbed" and hasattr(self, 'notebook') and self.notebook:
            # Clear all tabs
            for i in reversed(range(len(self.notebook.tabs()))):
                self.notebook.forget(i)
        elif self.current_view_mode == "paned":
            # Clear paned boxes
            for box in self.text_boxes:
                outer_frame = box.get("outer_frame")
                if outer_frame and outer_frame.winfo_exists():
                    outer_frame.destroy()
        
        # Clear the text_boxes list
        self.text_boxes = []

    def _save_to_onedrive_by_id(self, content, item_id, file_title):
        """Save content to an existing OneDrive file by item ID"""
        try:
            # Get the current file name to preserve it
            notes = self.onedrive_manager.list_notes()
            file_name = None
            for note in notes:
                if note.get("id") == item_id:
                    file_name = note.get("name")
                    break
            
            if not file_name:
                file_name = "note.json"  # Fallback
            
            # Create note data structure
            note_data = {
                "content": content,
                "last_modified": time.time(),
                "title": file_title.cget("text") if file_title else "Untitled"
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
                    name = note.get("name", "").replace(".json", "")
                    
                    try:
                        note_data = self.onedrive_manager.get_note_content(item_id)
                        if note_data:
                            content = note_data.get("content", "")
                            self.add_text_box(content=content, file_path=f"onedrive:{item_id}", onedrive_name=name)
                    except Exception as e:
                        messagebox.showerror("Error", f"Failed to open {name}: {e}")
                
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
                            self._save_to_onedrive_by_id(content, item_id, None)
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
                    self._save_to_onedrive_by_id(content, item_id, file_title)
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
                        # Delete placeholder depending on view
                        if self.current_view_mode == "tabbed" and getattr(self, 'notebook', None):
                            try:
                                nb = self.notebook
                                if nb is not None:
                                    nb.forget(0)
                            except Exception:
                                pass
                            self.text_boxes.pop(0)
                        elif self.current_view_mode == "paned":
                            outer = bx.get("outer_frame")
                            try:
                                if outer is not None:
                                    pw = getattr(self, 'paned_window', None)
                                    if pw is not None:
                                        pw.forget(outer)
                            except Exception:
                                pass
                            try:
                                if outer is not None:
                                    outer.destroy()
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
                self.text_boxes.append({
                    "text_box": text_widget,
                    "file_path": file_path,
                    "saved": True,
                    "title": os.path.basename(file_path) if file_path else "Untitled",
                    "tab_frame": tab_frame,
                    "font_size": base_font_size,
                })
                # Initialize last saved signature for accurate dirty tracking
                try:
                    self.text_boxes[-1]["last_saved_sig"] = self._compute_content_sig(text_widget)
                except Exception:
                    pass

                i = len(nb.tabs())
                file_name = os.path.basename(file_path) if file_path else f"Untitled {i+1}"
                tab_title = f"Tab {i+1}: {file_name}"
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
                
            elif self.current_view_mode == "paned":
                if self.paned_window is None:
                    messagebox.showinfo("Add Box", "Paned view is not available. Try switching to tabbed view first.")
                    return
                
            # Continue with paned mode logic
            # Create a new outer frame for the box
            pw = self.paned_window
            outer_frame = tk.Frame(pw, bd=2, relief=tk.RAISED)
            if pw is not None:
                pw.add(outer_frame, minsize=200)

            # Create the inner frame for content
            frame = tk.Frame(outer_frame)
            frame.pack(fill=tk.BOTH, expand=True)
            frame.grid_rowconfigure(1, weight=1)
            frame.grid_columnconfigure(1, weight=1)

            # Title label for the file
            file_name = os.path.basename(file_path) if file_path else "Untitled"
            file_title = tk.Label(frame, text=file_name, bg="lightgray")
            file_title.grid(row=0, column=0, columnspan=2, sticky="ew")

            # Button frame for controls
            button_frame = tk.Frame(frame)
            button_frame.grid(row=1, column=0, sticky="ns", padx=5, pady=5)

            # Text frame with scrollbar
            text_frame = tk.Frame(frame)
            text_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
            text_frame.grid_rowconfigure(0, weight=1)
            text_frame.grid_columnconfigure(0, weight=1)

            v_scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL)
            v_scrollbar.grid(row=0, column=1, sticky="ns")

            base_font_size = int(font_size) if font_size else 11
            text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=v_scrollbar.set, undo=True, font=("Consolas", base_font_size))
            text_widget.grid(row=0, column=0, sticky="nsew")
            v_scrollbar.config(command=text_widget.yview)

            # Insert content if provided
            if content:
                text_widget.insert("1.0", content)
            elif file_path and os.path.exists(file_path):
                try:
                    with open(file_path, "r", encoding="utf-8") as file:
                        file_content = file.read()
                    text_widget.insert("1.0", file_content)
                except Exception:
                    pass

            # Add control buttons with proper commands
            def make_close_cmd():
                return lambda: self.close_box(outer_frame, text_widget, file_path, file_title)
            def make_save_cmd():
                return lambda: self.save_box(text_widget, file_path, file_title)
            def make_load_cmd():
                return lambda: self.load_box(text_widget)
            def make_copy_cmd():
                return lambda: self.copy_to_clipboard(text_widget)

            tk.Button(button_frame, text="Close", command=make_close_cmd()).pack(fill=tk.X, pady=2)
            tk.Button(button_frame, text="Save", command=make_save_cmd()).pack(fill=tk.X, pady=2)
            tk.Button(button_frame, text="Load", command=make_load_cmd()).pack(fill=tk.X, pady=2)
            tk.Button(button_frame, text="Copy", command=make_copy_cmd()).pack(fill=tk.X, pady=2)

            # Ensure text box is editable and focusable
            text_widget.config(state=tk.NORMAL)
            text_widget.focus_set()
            
            # Debug: Print text widget configuration
            print(f"Text widget state: {text_widget.cget('state')}")
            print(f"Text widget can focus: {text_widget.focus_displayof() is not None}")
            
            # Test editability by trying to insert a character
            try:
                cursor_pos = text_widget.index(tk.INSERT)
                text_widget.insert(cursor_pos, "")  # Insert nothing, just test if it works
                print("Text widget is editable")
            except Exception as e:
                print(f"Text widget edit test failed: {e}")
            
            # Force the text widget to be ready for input
            text_widget.update_idletasks()
            self.root.update_idletasks()
            
            # Make sure no other bindings are interfering
            text_widget.bindtags((str(text_widget), "Text", ".", "all"))

            # --- Real-time spell checking ---
            spell_checker = None
            try:
                import re
                from spellchecker import SpellChecker
                spell_checker = SpellChecker()
                text_widget.tag_configure("misspelled", background="#FFFF00", foreground="#000000", underline=True)

                def check_spelling(event=None):
                    text = text_widget.get("1.0", tk.END)
                    words = re.findall(r"\b\w+\b", text)
                    misspelled = spell_checker.unknown(words)
                    print(f"Spell check called. Misspelled: {misspelled}")
                    text_widget.tag_remove("misspelled", "1.0", tk.END)
                    for word in misspelled:
                        # Use regex to find whole word positions
                        for match in re.finditer(rf"\b{re.escape(word)}\b", text, re.IGNORECASE):
                            start_idx = match.start()
                            end_idx = match.end()
                            # Convert string index to Tkinter index
                            start = f"1.0+{start_idx}c"
                            end = f"1.0+{end_idx}c"
                            text_widget.tag_add("misspelled", start, end)
                # Don't bind KeyRelease here - we'll handle it later with combined function
                check_spelling()
            except Exception as e:
                print(f"Spell check error: {e}")

            # Add right-click context menu with spell checking support
            try:
                self._add_context_menu(text_widget, spell_checker)
            except Exception as e:
                print(f"Error adding context menu: {e}")

            # --- Status bar update bindings ---
            def update_status_on_event(event=None):
                self._schedule_status_update()
            
            # Bind events that should trigger status updates - do this AFTER all other setup
            def create_status_updater():
                def update_status():
                    self._schedule_status_update()
                return update_status
            
            self.root.after_idle(lambda: self._setup_text_widget_bindings(text_widget, check_spelling, create_status_updater(), spell_checker))

            self.text_boxes.append({"text_widget": text_widget, "text_box": text_widget, "file_path": file_path, "file_title": file_title, "outer_frame": outer_frame, "saved": True})
            try:
                self.text_boxes[-1]["last_saved_sig"] = self._compute_content_sig(text_widget)
            except Exception:
                pass
            # Initialize label icon for saved state
            try:
                idx = len(self.text_boxes) - 1
                self._update_dirty_indicator(idx)
            except Exception:
                pass
            self.root.update_idletasks()
            
            if len(self.text_boxes) == 1:
                # Force the single box to fill all available height
                pw = self.paned_window
                paned_height = pw.winfo_height() if pw is not None else 0
                if paned_height < 10:
                    paned_height = self.root.winfo_height() - self.toolbar_main.winfo_height() - self.toolbar_dock.winfo_height()
                try:
                    if pw is not None:
                        pw.paneconfig(outer_frame, minsize=paned_height)
                except Exception:
                    pass
            else:
                self.equalize_boxes()
            
            # Update status bar after adding new box
            self._schedule_status_update()
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not add text box: {e}")

    def close_box(self, outer_frame: tk.Frame, text_box: tk.Text, file_path: str | None, file_title: tk.Label):
        self.save_box(text_box, file_path, file_title)
        pw = self.paned_window
        if pw is not None:
            pw.forget(outer_frame)
        outer_frame.destroy()
        try:
            if file_path and file_path not in self.recently_closed:
                self.recently_closed.append(file_path)
            self.text_boxes = [b for b in self.text_boxes if b.get("outer_frame") is not outer_frame]
            # Update status bar after closing box
            self._schedule_status_update()
        except Exception:
            pass

    def _minimize_box(self, outer_frame):
        try:
            pw = self.paned_window
            if not pw:
                return
            pw.paneconfig(outer_frame, minsize=40)
            idx = pw.panes().index(outer_frame)
            if idx < len(pw.panes()) - 1:
                pw.sash_place(idx, 0, 40 * (idx + 1))
        except Exception:
            pass

    def _maximize_box(self, outer_frame):
        try:
            pw = self.paned_window
            if not pw:
                return
            panes = pw.panes()
            total_height = pw.winfo_height()
            if total_height < 100:
                total_height = self.root.winfo_height() - self.toolbar_main.winfo_height() - self.toolbar_dock.winfo_height() - 20
            for pane in panes:
                if pane == outer_frame:
                    pw.paneconfig(pane, minsize=total_height)
                else:
                    pw.paneconfig(pane, minsize=40)
            idx = panes.index(outer_frame)
            y = 0
            for i in range(len(panes) - 1):
                if i < idx:
                    y += 40
                    pw.sash_place(i, 0, y)
                else:
                    y = total_height - 40 * (len(panes) - i - 1)
                    pw.sash_place(i, 0, y)
        except Exception:
            pass

    def equalize_boxes(self):
        print("DEBUG: Equalize boxes button clicked!")
        # No-op in tabbed mode
        if getattr(self, 'current_view_mode', None) != 'paned':
            print("DEBUG: Equalize ignored in tabbed mode")
            return
        
        # Check current arrangement mode
        if hasattr(self, 'current_arrangement') and self.current_arrangement == "horizontal":
            print("DEBUG: In horizontal mode - equalizing box widths")
            self._apply_arrangement_change()  # <-- Fixed: Use existing method
            return
        
        # Continue with vertical equalization for vertical mode
        print("DEBUG: In vertical mode - equalizing box heights")
        pw = getattr(self, 'paned_window', None)
        if not pw or not pw.winfo_exists():
            print("DEBUG: No valid paned_window to equalize")
            return
        self.root.update_idletasks()
        num_panes = len(pw.panes())
        print(f"DEBUG: Number of panes: {num_panes}")
        
        if num_panes > 1:
            # Force the paned window to use all available space
            root_height = self.root.winfo_height()
            toolbar_main_height = self.toolbar_main.winfo_height()
            toolbar_dock_height = self.toolbar_dock.winfo_height()
            
            # Calculate maximum available height for the paned window
            available_height = root_height - toolbar_main_height - toolbar_dock_height - 20
            
            # Use the available height, not the current paned window height
            total_height = max(available_height, 200)  # Minimum 200px total
            pane_height = max(60, total_height // num_panes)  # Minimum 60px per pane
            print(f"DEBUG: Using total height: {total_height}, pane height: {pane_height}")
            
            # Reset all pane minsize values first
            print("DEBUG: Resetting minsize values...")
            for pane in pw.panes():
                try:
                    if pw and pw.winfo_exists():
                        pw.paneconfig(pane, minsize=1)
                except Exception as e:
                    print(f"DEBUG: Error resetting minsize: {e}")
            
            # Force update before placing sashes
            self.root.update_idletasks()
            
            # Place sashes to use the full available height
            y = 0
            print("DEBUG: Placing sashes for full height utilization...")
            for i in range(num_panes - 1):
                y += pane_height
                print(f"DEBUG: Setting sash {i} at position {y}")
                if pw and pw.winfo_exists():
                    pw.sash_place(i, 0, y)
            
            # Force another update
            self.root.update_idletasks()
            
            # Set minsize for each pane to maintain heights
            print("DEBUG: Setting minsize values...")
            for pane in pw.panes():
                try:
                    if pw and pw.winfo_exists():
                        pw.paneconfig(pane, minsize=pane_height)
                    print(f"DEBUG: Set pane minsize to {pane_height}")
                except Exception as e:
                    print(f"DEBUG: Error setting minsize: {e}")
                    
        elif num_panes == 1:
            print("DEBUG: Single pane - maximizing to full height")
            pw = self.paned_window
            if not pw or not pw.winfo_exists():
                return
            pane = pw.panes()[0]
            root_height = self.root.winfo_height()
            toolbar_main_height = self.toolbar_main.winfo_height()
            toolbar_dock_height = self.toolbar_dock.winfo_height()
            available_height = root_height - toolbar_main_height - toolbar_dock_height - 20
            
            try:
                if pw and pw.winfo_exists():
                    pw.paneconfig(pane, minsize=max(available_height, 200))
                print(f"DEBUG: Set single pane to {max(available_height, 200)}px")
            except Exception as e:
                print(f"DEBUG: Error setting single pane: {e}")
        else:
            print("DEBUG: No panes found!")
        
        # Final update
        self.root.update_idletasks()
        print("DEBUG: Vertical equalization completed")

    def toggle_tabbed_view(self):
        """Toggle between paned and tabbed view modes."""
        try:
            if self.current_view_mode == "paned":
                self._switch_to_tabbed_view()
            elif self.current_view_mode == "tabbed":
                self._switch_to_paned_view()
        except Exception as e:
            print(f"DEBUG: Error toggling view: {e}")

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

                    # Store tab data in text_boxes array for proper tracking
                    self.text_boxes.append({
                        "text_box": text_widget,
                        "file_path": data.get("file_path", ""),
                        "saved": data.get("saved", True),
                        "title": data.get("title", "Untitled"),
                        "tab_frame": tab_frame,
                        "tab_index": i
                    })
                    try:
                        self.text_boxes[-1]["last_saved_sig"] = self._compute_content_sig(text_widget) if self.text_boxes[-1]["saved"] else ""
                    except Exception:
                        pass

                    # Generate simple tab title
                    file_name = os.path.basename(data.get("file_path") or "") or f"Untitled {i+1}"
                    tab_title = f"Tab {i+1}: {file_name}"

                    # Create a small colored square icon for the tab for readable color indication
                    # Add tab with icon reflecting saved state
                    try:
                        normal_icon, dirty_icon = self._get_or_create_tab_icons(i)
                        icon_to_use = normal_icon if self.text_boxes[i]["saved"] else dirty_icon
                        self.notebook.add(tab_frame, text=tab_title, image=icon_to_use, compound="left")
                    except Exception:
                        # Fallback without image if PhotoImage fails
                        self.notebook.add(tab_frame, text=tab_title)
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
            # Try to restore paned view if tabbed view fails
            try:
                self.current_view_mode = "paned"
                self._switch_to_paned_view()
            except:
                pass

    def _switch_to_paned_view(self):
        """Switch from tabbed view to paned view."""
        print("DEBUG: Starting paned view switch")
        
        try:
            # Store current content from tabs before destroying notebook
            saved_data = []
            
            if hasattr(self, 'notebook') and self.notebook:
                print("DEBUG: Collecting data from tabs")
                
                # Get data from current text_boxes (which should contain tab data)
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
                            print(f"DEBUG: Saved data from tab: {len(content)} chars, file_path: '{file_path}', title: '{title}'")
                        except Exception as e:
                            print(f"DEBUG: Error getting content from tab: {e}")
                
                # Destroy the notebook
                try:
                    print("DEBUG: Destroying notebook")
                    self.notebook.destroy()
                    self.notebook = None
                except Exception as e:
                    print(f"DEBUG: Error destroying notebook: {e}")
            
            print(f"DEBUG: Collected {len(saved_data)} tabs of data")
            
            # Create new paned window
            print("DEBUG: Creating paned window")
            orient = tk.HORIZONTAL if hasattr(self, 'current_arrangement') and self.current_arrangement == "horizontal" else tk.VERTICAL
            self.paned_window = tk.PanedWindow(self.root, orient=orient, sashwidth=5, sashrelief=tk.RAISED)
            self.paned_window.pack(fill=tk.BOTH, expand=True)
            
            # Clear text_boxes and recreate as panes
            self.text_boxes = []
            
            print(f"DEBUG: Creating {len(saved_data)} panes")
            
            for i, data in enumerate(saved_data):
                try:
                    print(f"DEBUG: Creating pane {i+1}")
                    
                    # Create a new outer frame for the pane
                    outer_frame = tk.Frame(self.paned_window, bd=2, relief=tk.RAISED)
                    self.paned_window.add(outer_frame, minsize=200)

                    # Create the inner frame for content
                    frame = tk.Frame(outer_frame)
                    frame.pack(fill=tk.BOTH, expand=True)
                    frame.grid_rowconfigure(1, weight=1)
                    frame.grid_columnconfigure(1, weight=1)

                    # Title label for the file
                    file_name = os.path.basename(data.get("file_path") or "") or f"Untitled {i+1}"
                    file_title = tk.Label(frame, text=file_name, bg="lightgray")
                    file_title.grid(row=0, column=0, columnspan=2, sticky="ew")

                    # Button frame for controls
                    button_frame = tk.Frame(frame)
                    button_frame.grid(row=1, column=0, sticky="ns", padx=5, pady=5)

                    # Text frame with scrollbar
                    text_frame = tk.Frame(frame)
                    text_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
                    text_frame.grid_rowconfigure(0, weight=1)
                    text_frame.grid_columnconfigure(0, weight=1)

                    v_scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL)
                    v_scrollbar.grid(row=0, column=1, sticky="ns")

                    text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=v_scrollbar.set, undo=True)
                    text_widget.grid(row=0, column=0, sticky="nsew")
                    v_scrollbar.config(command=text_widget.yview)

                    # Insert the saved content
                    if data.get("content"):
                        text_widget.insert("1.0", data["content"])
                        print(f"DEBUG: Inserted {len(data['content'])} chars into pane {i+1}")

                    # Add control buttons with proper closure to capture current iteration values
                    def make_close_cmd(frame=outer_frame, widget=text_widget, path=data.get("file_path"), title=file_title):
                        return lambda: self.close_box(frame, widget, path, title)
                    def make_save_cmd(widget=text_widget, path=data.get("file_path"), title=file_title):
                        return lambda: self.save_box(widget, path, title)
                    def make_load_cmd(widget=text_widget):
                        return lambda: self.load_box(widget)
                    def make_copy_cmd(widget=text_widget):
                        return lambda: self.copy_to_clipboard(widget)

                    tk.Button(button_frame, text="Close", command=make_close_cmd()).pack(fill=tk.X, pady=2)
                    tk.Button(button_frame, text="Save", command=make_save_cmd()).pack(fill=tk.X, pady=2)
                    tk.Button(button_frame, text="Load", command=make_load_cmd()).pack(fill=tk.X, pady=2)
                    tk.Button(button_frame, text="Copy", command=make_copy_cmd()).pack(fill=tk.X, pady=2)

                    self.text_boxes.append({
                        "text_box": text_widget,
                        "file_path": data.get("file_path"),
                        "saved": data.get("saved", True),
                        "title": data.get("title"),
                        "file_title": file_title,
                        "outer_frame": outer_frame
                    })
                    try:
                        self.text_boxes[-1]["last_saved_sig"] = self._compute_content_sig(text_widget) if self.text_boxes[-1]["saved"] else ""
                    except Exception:
                        pass
                    
                    print(f"DEBUG: Successfully created pane {i+1}")
                    
                except Exception as e:
                    print(f"DEBUG: Error creating pane {i+1}: {e}")
                    import traceback
                    traceback.print_exc()

            # After creating all panes, ensure indicators match saved flags
            try:
                for idx in range(len(self.text_boxes)):
                    self._update_dirty_indicator(idx)
            except Exception:
                pass

            # Update view mode and status
            self.current_view_mode = "paned"
            try:
                if hasattr(self, 'status_bar'):
                    self.status_bar.config(text=f"View: Paned ({len(self.text_boxes)} boxes)")
                    self.root.after(2000, self._schedule_status_update)
            except Exception as e:
                print(f"DEBUG: Error updating status bar: {e}")
                
            print(f"DEBUG: Successfully switched to paned view with {len(self.text_boxes)} boxes")
        
        except Exception as e:
            print(f"ERROR: Failed to switch to paned view: {e}")
            import traceback
            traceback.print_exc()

    def _apply_custom_tab_colors(self):
        """Color overlay functionality disabled - tabs now use plain grey styling only."""
        pass

    def _update_tab_title(self, tab_index, file_path):
        """Update the title of a specific tab with simple text."""
        try:
            if 0 <= tab_index < len(self.text_boxes) and self.notebook:
                box_data = self.text_boxes[tab_index]
                
                # Create simple title
                file_name = os.path.basename(file_path) if file_path else f"Untitled {tab_index+1}"
                tab_title = f"Tab {tab_index+1}: {file_name}"
                
                # Update the notebook tab if possible
                try:
                    if not box_data.get("saved", True):
                        tab_title = tab_title + " *"
                    self.notebook.tab(tab_index, text=tab_title)
                    print(f"DEBUG: Updated tab {tab_index} title to: {tab_title}")
                except:
                    print(f"DEBUG: Could not update tab title for tab {tab_index}")
                
        except Exception as e:
            print(f"Error updating tab title: {e}")

    def close_all_boxes(self):
        """Close all text boxes and clear the layout."""
        try:
            # Proceed without confirmation
            for box in self.text_boxes:
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
            try:
                if os.path.exists(self.layout_file):
                    os.remove(self.layout_file)
            except Exception:
                pass
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
                "view_mode": getattr(self, 'current_view_mode', 'paned'),
                "arrangement": getattr(self, 'current_arrangement', 'vertical'),
                "boxes": []
            }

            # Save data for each text box (persist content to restore unsaved notes; file_path if present)
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

            # Save pane sizes if in paned mode and panes exist
            try:
                pw = getattr(self, 'paned_window', None)
                if self.current_view_mode == 'paned' and pw and pw.winfo_exists():
                    sizes = []
                    for box_data in self.text_boxes:
                        outer = box_data.get("outer_frame")
                        if outer and outer.winfo_exists():
                            sizes.append(int(max(1, outer.winfo_height())))
                    if sizes:
                        layout_data["pane_sizes"] = sizes
            except Exception:
                pass

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

            # Basic bindings for text editing with spell check
            text_widget.bind("<KeyRelease>", on_change)
            text_widget.bind("<Button-1>", on_change)
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
                status_text = f"Boxes: {len(self.text_boxes)} | View: {self.current_view_mode} | {current_time}"
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
        # Ensure arrays are long enough
        while len(self._tab_icons) <= index:
            self._tab_icons.append(None)
        while len(self._tab_dirty_icons) <= index:
            self._tab_dirty_icons.append(None)
        try:
            color = self._get_tab_color_for_index(index)
        except Exception:
            color = "#C0C0C0"
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
                # Optionally add asterisk to text title for clarity
                try:
                    file_path = box.get("file_path")
                    file_name = os.path.basename(file_path) if file_path else f"Untitled {index+1}"
                    title = f"Tab {index+1}: {file_name}{'' if saved else ' *'}"
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
        """Handle window close: save files, layout, and geometry with OneDrive sync."""
        try:
            # Special handling for OneDrive authenticated users
            if self.onedrive_manager and self.onedrive_manager.is_authenticated():
                self._save_all_to_onedrive_on_exit()
            else:
                self._save_all_open_files()
        except Exception:
            pass
        try:
            # For OneDrive users, don't save local layout since notes are in cloud
            if not (self.onedrive_manager and self.onedrive_manager.is_authenticated()):
                self.save_layout_to_file()
        except Exception:
            pass
        try:
            self._persist_geometry()
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
        """Rename the underlying file (if it exists) and update titles."""
        try:
            if tab_index < 0 or tab_index >= len(self.text_boxes):
                return
            box = self.text_boxes[tab_index]
            current_path = box.get("file_path") or ""
            default_name = os.path.basename(current_path) if current_path else (box.get("title") or f"Untitled {tab_index+1}")
            try:
                from tkinter import simpledialog
                new_name = simpledialog.askstring("Rename", "New name for this note/file:", initialvalue=default_name, parent=self.root)
            except Exception:
                new_name = None
            if not new_name or new_name.strip() == default_name:
                return
            new_name = new_name.strip()

            # If there's an existing file, rename on disk within the same folder
            if current_path and os.path.exists(current_path):
                new_path = os.path.join(os.path.dirname(current_path), new_name)
                try:
                    os.replace(current_path, new_path)
                    box["file_path"] = new_path
                except Exception as e:
                    messagebox.showerror("Rename Error", f"Could not rename file: {e}")
                    return

            # Update UI: box title label and tab title
            box["title"] = new_name
            file_title = box.get("file_title")
            if file_title and file_title.winfo_exists():
                try:
                    file_title.config(text=new_name)
                except Exception:
                    pass
            if self.current_view_mode == "tabbed" and self.notebook:
                try:
                    self.notebook.tab(tab_index, text=new_name)
                except Exception:
                    pass
            # Persist layout
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
                           f"Configuration files are stored in:\n\n{config_dir}\n\n"
                           f"Layout file: {os.path.basename(self.layout_file)}\n"
                           f"Config file: {os.path.basename(self.config_file)}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not show configuration location: {e}")

    def cycle_box_arrangement(self):
        """Cycle through different box arrangement modes."""
        try:
            print("DEBUG: Cycling box arrangement")
            
            # Only allow arrangement changes in paned mode (silent no-op otherwise)
            if self.current_view_mode != "paned":
                print("DEBUG: Arrangement ignored in tabbed mode")
                return
            
            # Check if we have a valid paned window
            if not self.paned_window or not self.paned_window.winfo_exists():
                print("DEBUG: No valid paned window exists; arrangement ignored")
                return
            
            # Cycle through arrangements
            if self.current_arrangement == "horizontal":
                self.current_arrangement = "vertical"
                print("DEBUG: Switching to vertical arrangement")
                self._apply_arrangement_change()
            else:
                self.current_arrangement = "horizontal"
                print("DEBUG: Switching to horizontal arrangement")
                self._apply_arrangement_change()
                
        except Exception as e:
            # Silent failure (no dialogs) as requested
            print(f"DEBUG: Error cycling arrangement (suppressed dialog): {e}")

    def _apply_arrangement_change(self):
        """Apply the current arrangement mode to the paned window."""
        try:
            print(f"DEBUG: Applying {self.current_arrangement} arrangement")
            
            # Save current content before rearranging - with widget validation
            saved_data = []
            for box_data in self.text_boxes:
                text_widget = box_data.get("text_box")
                if text_widget:
                    try:
                        # Validate widget still exists and is accessible
                        if text_widget.winfo_exists():
                            content = text_widget.get("1.0", tk.END)
                            saved_data.append({
                                "content": content,
                                "file_path": box_data.get("file_path", ""),
                                "saved": box_data.get("saved", True),
                                "title": box_data.get("title", "Untitled")
                            })
                    except tk.TclError as e:
                        print(f"DEBUG: Widget no longer exists: {e}")
                        # Widget destroyed, skip it
                        continue
                    except Exception as e:
                        print(f"DEBUG: Error accessing widget: {e}")
                        continue
            
            
            if not saved_data:
                print("DEBUG: No data to rearrange")
                return

            # Destroy current paned window safely
            if self.paned_window:
                try:
                    if self.paned_window.winfo_exists():
                        self.paned_window.destroy()
                except tk.TclError:
                    print("DEBUG: Paned window already destroyed")
                self.paned_window = None            # Create new paned window with correct orientation
            orient = tk.HORIZONTAL if self.current_arrangement == "horizontal" else tk.VERTICAL
            self.paned_window = tk.PanedWindow(self.root, orient=orient, sashwidth=5, sashrelief=tk.RAISED)
            self.paned_window.pack(fill=tk.BOTH, expand=True)
            
            # Clear and recreate text boxes
            self.text_boxes = []

            print(f"DEBUG: Creating {len(saved_data)} panes")
            
            for i, data in enumerate(saved_data):
                try:
                    print(f"DEBUG: Creating pane {i+1}")
                    
                    # Create a new outer frame for the pane
                    outer_frame = tk.Frame(self.paned_window, bd=2, relief=tk.RAISED)
                    self.paned_window.add(outer_frame, minsize=200)

                    # Create the inner frame for content
                    frame = tk.Frame(outer_frame)
                    frame.pack(fill=tk.BOTH, expand=True)
                    frame.grid_rowconfigure(1, weight=1)
                    frame.grid_columnconfigure(1, weight=1)

                    # Title label for the file
                    file_name = os.path.basename(data.get("file_path") or "") or f"Untitled {i+1}"
                    file_title = tk.Label(frame, text=file_name, bg="lightgray")
                    file_title.grid(row=0, column=0, columnspan=2, sticky="ew")

                    # Button frame for controls
                    button_frame = tk.Frame(frame)
                    button_frame.grid(row=1, column=0, sticky="ns", padx=5, pady=5)

                    # Text frame with scrollbar
                    text_frame = tk.Frame(frame)
                    text_frame.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
                    text_frame.grid_rowconfigure(0, weight=1)
                    text_frame.grid_columnconfigure(0, weight=1)

                    v_scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL)
                    v_scrollbar.grid(row=0, column=1, sticky="ns")

                    text_widget = tk.Text(text_frame, wrap=tk.WORD, yscrollcommand=v_scrollbar.set, undo=True)
                    text_widget.grid(row=0, column=0, sticky="nsew")
                    v_scrollbar.config(command=text_widget.yview)

                    # Insert the saved content
                    if data.get("content"):
                        text_widget.insert("1.0", data["content"])
                        print(f"DEBUG: Inserted {len(data['content'])} chars into pane {i+1}")

                    # Add control buttons with proper closure to capture current iteration values
                    def make_close_cmd(frame=outer_frame, widget=text_widget, path=data.get("file_path"), title=file_title):
                        return lambda: self.close_box(frame, widget, path, title)
                    def make_save_cmd(widget=text_widget, path=data.get("file_path"), title=file_title):
                        return lambda: self.save_box(widget, path, title)
                    def make_load_cmd(widget=text_widget):
                        return lambda: self.load_box(widget)
                    def make_copy_cmd(widget=text_widget):
                        return lambda: self.copy_to_clipboard(widget)

                    tk.Button(button_frame, text="Close", command=make_close_cmd()).pack(fill=tk.X, pady=2)
                    tk.Button(button_frame, text="Save", command=make_save_cmd()).pack(fill=tk.X, pady=2)
                    tk.Button(button_frame, text="Load", command=make_load_cmd()).pack(fill=tk.X, pady=2)
                    tk.Button(button_frame, text="Copy", command=make_copy_cmd()).pack(fill=tk.X, pady=2)

                    self.text_boxes.append({
                        "text_box": text_widget,
                        "file_path": data.get("file_path"),
                        "saved": data.get("saved", True),
                        "title": data.get("title"),
                        "file_title": file_title,
                        "outer_frame": outer_frame
                    })
                    
                    print(f"DEBUG: Successfully created pane {i+1}")
                    
                except Exception as e:
                    print(f"DEBUG: Error creating pane {i+1}: {e}")
                    import traceback
                    traceback.print_exc()

            # Update view mode and status
            self.current_view_mode = "paned"
            try:
                self.status_bar.config(text=f"View: Paned ({len(self.text_boxes)} boxes)")
                self.root.after(2000, self._schedule_status_update)
            except Exception as e:
                print(f"DEBUG: Error updating status bar: {e}")
                
            print(f"DEBUG: Successfully switched to paned view with {len(self.text_boxes)} boxes")
        
        except Exception as e:
            print(f"ERROR: Failed to apply arrangement change: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    root = tk.Tk()
    app = EditableBoxApp(root)
    root.mainloop()
