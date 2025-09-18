#!/usr/bin/env python3
"""
Mobile Noted - Android-compatible note-taking app
Converted from desktop tkinter version to Kivy for mobile use
"""

import os
import json
import uuid
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

try:
    import enchant
    SPELLCHECK_AVAILABLE = True
except ImportError:
    SPELLCHECK_AVAILABLE = False
    print("Warning: pyenchant not installed. Spellcheck disabled.")

# Import OneDrive manager for cloud sync
try:
    from onedrive_manager import OneDriveManager
    ONEDRIVE_AVAILABLE = True
except ImportError:
    OneDriveManager = None
    ONEDRIVE_AVAILABLE = False
    print("Warning: OneDriveManager not available. Cloud sync disabled.")

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.switch import Switch
from kivy.uix.spinner import Spinner
from kivy.uix.slider import Slider
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform
from kivy.logger import Logger
from kivy.graphics import Line, Color, Rectangle
from kivy.core.text import Label as CoreLabel

# Configure minimum Kivy version
kivy.require('2.0.0')


class SpellCheckTextInput(TextInput):
    """TextInput with live spellchecking functionality."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize spellchecker
        self.spell_checker = None
        self.misspelled_words = set()
        self.spell_check_enabled = SPELLCHECK_AVAILABLE
        
        if SPELLCHECK_AVAILABLE:
            try:
                self.spell_checker = enchant.Dict("en_US")
            except enchant.DictNotFoundError:
                try:
                    self.spell_checker = enchant.Dict("en")
                except enchant.DictNotFoundError:
                    self.spell_check_enabled = False
                    Logger.warning("SpellCheck: No English dictionary found")
        
        # Bind text change event for live checking
        if self.spell_check_enabled:
            self.bind(text=self._on_text_spell_check)
            self.bind(cursor_pos=self._update_spell_highlights)
            self.bind(size=self._update_spell_highlights)
            self.bind(pos=self._update_spell_highlights)
    
    def _on_text_spell_check(self, instance, text):
        """Check spelling as text changes."""
        if not self.spell_check_enabled:
            return
        
        # Schedule spell check to avoid too frequent updates
        Clock.unschedule(self._perform_spell_check)
        Clock.schedule_once(lambda dt: self._perform_spell_check(), 0.5)
    
    def _perform_spell_check(self):
        """Perform the actual spell checking."""
        if not self.spell_check_enabled or not self.text:
            self.misspelled_words.clear()
            self._update_spell_highlights()
            return
        
        # Extract words (letters, numbers, apostrophes)
        words = re.findall(r"[a-zA-Z][a-zA-Z']*", self.text)
        self.misspelled_words.clear()
        
        for word in words:
            if len(word) > 1 and not self.spell_checker.check(word):
                # Find all occurrences of this word
                start = 0
                while True:
                    pos = self.text.find(word, start)
                    if pos == -1:
                        break
                    # Check if it's a whole word (not part of another word)
                    if (pos == 0 or not self.text[pos-1].isalpha()) and \
                       (pos + len(word) >= len(self.text) or not self.text[pos + len(word)].isalpha()):
                        self.misspelled_words.add((pos, pos + len(word)))
                    start = pos + 1
        
        self._update_spell_highlights()
    
    def _update_spell_highlights(self, *args):
        """Update the visual highlights for misspelled words."""
        if not self.spell_check_enabled:
            return
        
        # Clear existing highlights
        self.canvas.after.clear()
        
        if not self.misspelled_words:
            return
        
        # Add red underlines for misspelled words
        with self.canvas.after:
            Color(1, 0, 0, 0.8)  # Red color with transparency
            
            for start_pos, end_pos in self.misspelled_words:
                # Get the position of the word in the text input
                try:
                    # Convert text position to pixel coordinates
                    start_x, start_y = self._get_text_pos(start_pos)
                    end_x, end_y = self._get_text_pos(end_pos)
                    
                    # Draw underline
                    Line(points=[start_x, start_y - 2, end_x, end_y - 2], width=2)
                except:
                    # Skip if position calculation fails
                    pass
    
    def _get_text_pos(self, text_index):
        """Get pixel position for a character index in the text."""
        if text_index > len(self.text):
            text_index = len(self.text)
        
        # Get text up to the index
        text_before = self.text[:text_index]
        
        # Create a label to measure text dimensions
        label = CoreLabel(text=text_before, font_size=self.font_size, font_name=self.font_name)
        label.refresh()
        
        # Calculate position relative to text input
        x = self.x + self.padding[0]
        y = self.y + self.height - self.padding[1] - label.texture.height
        
        return x + label.texture.width, y
    
    def get_spelling_suggestions(self, word):
        """Get spelling suggestions for a misspelled word."""
        if not self.spell_check_enabled or not word:
            return []
        
        try:
            return self.spell_checker.suggest(word)[:5]  # Return top 5 suggestions
        except:
            return []
    
    def on_touch_down(self, touch):
        """Handle touch events for spell check context menu."""
        if touch.button == 'right' and self.spell_check_enabled:
            # Check if touch is on a misspelled word
            word_at_pos = self._get_word_at_position(touch.pos)
            if word_at_pos:
                self._show_spell_suggestions(word_at_pos, touch.pos)
                return True
        
        return super().on_touch_down(touch)
    
    def _get_word_at_position(self, pos):
        """Get the word at the given touch position if it's misspelled."""
        # This is a simplified implementation
        # In practice, you'd need to calculate the exact character position
        # For now, we'll return None to avoid complexity
        return None
    
    def _show_spell_suggestions(self, word, pos):
        """Show spelling suggestions in a popup."""
        suggestions = self.get_spelling_suggestions(word)
        if not suggestions:
            return
        
        # Create popup with suggestions (simplified)
        content = BoxLayout(orientation='vertical')
        for suggestion in suggestions:
            btn = Button(text=suggestion, size_hint_y=None, height=40)
            btn.bind(on_press=lambda x, s=suggestion: self._replace_word(word, s))
            content.add_widget(btn)
        
        popup = Popup(title=f'Suggestions for "{word}"', content=content, 
                     size_hint=(0.6, 0.8))
        popup.open()
    
    def _replace_word(self, old_word, new_word):
        """Replace misspelled word with suggestion."""
        self.text = self.text.replace(old_word, new_word, 1)
    
    def toggle_spell_check(self, enabled):
        """Enable or disable spell checking."""
        self.spell_check_enabled = enabled and SPELLCHECK_AVAILABLE
        if not self.spell_check_enabled:
            self.misspelled_words.clear()
            self._update_spell_highlights()
        else:
            self._perform_spell_check()


class NoteCard(BoxLayout):
    """Individual note card widget."""
    
    def __init__(self, note_data: Dict[str, Any], app_instance, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.spacing = 5
        self.size_hint_y = None
        self.height = 300
        self.padding = [10, 10, 10, 10]
        
        self.note_data = note_data
        self.app_instance = app_instance
        self.note_id = note_data.get('id', str(uuid.uuid4()))
        
        # State tracking for minimize/maximize
        self.is_minimized = False
        self.is_maximized = False
        self.original_height = 300
        self.minimized_height = 60
        
        # Create the UI
        self._create_note_ui()
        
        # Load content
        self._load_note_content()
    
    def _create_note_ui(self):
        """Create the note card user interface."""
        # Header with title and controls
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        
        # Title label (filename or "New Note")
        self.title_label = Label(
            text=self.note_data.get('title', 'New Note'),
            size_hint_x=0.6,
            halign='left',
            text_size=(None, None)
        )
        self.title_label.bind(size=self._update_title_text_size)
        header.add_widget(self.title_label)
        
        # Control buttons
        controls = BoxLayout(orientation='horizontal', size_hint_x=0.4, spacing=3)
        
        minimize_btn = Button(text='_', size_hint_x=0.2, height=35)
        minimize_btn.bind(on_press=self._minimize_note)
        controls.add_widget(minimize_btn)
        
        maximize_btn = Button(text='□', size_hint_x=0.2, height=35)
        maximize_btn.bind(on_press=self._maximize_note)
        controls.add_widget(maximize_btn)
        
        save_btn = Button(text='S', size_hint_x=0.2, height=35)
        save_btn.bind(on_press=self._save_note)
        controls.add_widget(save_btn)
        
        load_btn = Button(text='L', size_hint_x=0.2, height=35)
        load_btn.bind(on_press=self._load_note)
        controls.add_widget(load_btn)
        
        delete_btn = Button(text='X', size_hint_x=0.2, height=35)
        delete_btn.bind(on_press=self._delete_note)
        controls.add_widget(delete_btn)
        
        header.add_widget(controls)
        self.add_widget(header)
        
        # Text input area with scrollbar
        self.scroll_view = ScrollView(
            size_hint_y=None,
            height=250,
            bar_width=10,
            bar_color=[0.2, 0.5, 0.8, 0.8],  # Blue scrollbar
            bar_inactive_color=[0.5, 0.5, 0.5, 0.5],  # Gray when inactive
            scroll_type=['bars', 'content'],
            effect_cls='ScrollEffect',
            always_overscroll=False
        )
        
        self.text_input = SpellCheckTextInput(
            multiline=True,
            text=self.note_data.get('content', ''),
            font_size=16,
            size_hint_y=None,
            height=500,  # Make it taller than the ScrollView to enable scrolling
            do_wrap=True  # Enable text wrapping
        )
        self.text_input.bind(text=self._on_text_change)
        self.text_input.bind(width=self._update_text_width)
        
        self.scroll_view.add_widget(self.text_input)
        self.add_widget(self.scroll_view)
    
    def _update_title_text_size(self, instance, size):
        """Update text size for proper text wrapping."""
        instance.text_size = (size[0], None)
    
    def _update_text_width(self, instance, width):
        """Update text input width for proper text wrapping and scrolling."""
        # Set text_size to enable proper text wrapping in TextInput
        instance.text_size = (width, None)
        # The height will expand naturally when text wraps, triggering scrollbars
    
    def _on_text_change(self, instance, text):
        """Handle text changes for auto-save."""
        self.note_data['content'] = text
        self.note_data['modified'] = datetime.now().isoformat()
        
        # Trigger auto-save if enabled
        if self.app_instance.auto_save_enabled:
            Clock.unschedule(self._delayed_save)
            Clock.schedule_once(self._delayed_save, 2.0)  # Save after 2 seconds of inactivity
    
    def _delayed_save(self, dt):
        """Delayed auto-save function."""
        self._save_note_data()
    
    def _save_note(self, instance):
        """Save note to file."""
        if not self.text_input.text.strip():
            self.app_instance.show_message("Empty Note", "Cannot save empty note.")
            return
        
        # Create file chooser popup for saving
        content = BoxLayout(orientation='vertical')
        
        # File name input
        filename_input = TextInput(
            text=self.note_data.get('filename', f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"),
            size_hint_y=None,
            height=40,
            multiline=False
        )
        content.add_widget(Label(text='Filename:', size_hint_y=None, height=30))
        content.add_widget(filename_input)
        
        # Buttons
        buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        def save_file(instance):
            filename = filename_input.text.strip()
            if filename:
                if not filename.endswith('.txt'):
                    filename += '.txt'
                
                filepath = os.path.join(self.app_instance.notes_directory, filename)
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(self.text_input.text)
                    
                    self.note_data['filename'] = filename
                    self.note_data['filepath'] = filepath
                    self.title_label.text = filename
                    self._save_note_data()
                    
                    popup.dismiss()
                    self.app_instance.show_message("Success", f"Note saved as {filename}")
                except Exception as e:
                    self.app_instance.show_message("Error", f"Failed to save: {str(e)}")
            else:
                self.app_instance.show_message("Error", "Please enter a filename")
        
        save_button = Button(text='Save')
        save_button.bind(on_press=save_file)
        cancel_button = Button(text='Cancel')
        
        buttons.add_widget(save_button)
        buttons.add_widget(cancel_button)
        content.add_widget(buttons)
        
        popup = Popup(title='Save Note', content=content, size_hint=(0.9, 0.5))
        cancel_button.bind(on_press=popup.dismiss)
        popup.open()
    
    def _load_note(self, instance):
        """Load note from file."""
        content = BoxLayout(orientation='vertical')
        
        # File chooser
        file_chooser = FileChooserListView(
            path=self.app_instance.notes_directory,
            filters=['*.txt']
        )
        content.add_widget(file_chooser)
        
        # Buttons
        buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        def load_file(instance):
            if file_chooser.selection:
                filepath = file_chooser.selection[0]
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content_text = f.read()
                    
                    self.text_input.text = content_text
                    self.note_data['content'] = content_text
                    self.note_data['filename'] = os.path.basename(filepath)
                    self.note_data['filepath'] = filepath
                    self.title_label.text = os.path.basename(filepath)
                    self._save_note_data()
                    
                    popup.dismiss()
                    self.app_instance.show_message("Success", f"Loaded {os.path.basename(filepath)}")
                except Exception as e:
                    self.app_instance.show_message("Error", f"Failed to load: {str(e)}")
            else:
                self.app_instance.show_message("Error", "Please select a file")
        
        load_button = Button(text='Load')
        load_button.bind(on_press=load_file)
        cancel_button = Button(text='Cancel')
        
        buttons.add_widget(load_button)
        buttons.add_widget(cancel_button)
        content.add_widget(buttons)
        
        popup = Popup(title='Load Note', content=content, size_hint=(0.9, 0.8))
        cancel_button.bind(on_press=popup.dismiss)
        popup.open()
    
    def _delete_note(self, instance):
        """Delete this note."""
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text='Are you sure you want to delete this note?'))
        
        buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        def confirm_delete(instance):
            self.app_instance.delete_note(self.note_id)
            popup.dismiss()
        
        yes_button = Button(text='Yes')
        yes_button.bind(on_press=confirm_delete)
        no_button = Button(text='No')
        
        buttons.add_widget(yes_button)
        buttons.add_widget(no_button)
        content.add_widget(buttons)
        
        popup = Popup(title='Delete Note', content=content, size_hint=(0.6, 0.4))
        no_button.bind(on_press=popup.dismiss)
        popup.open()
    
    def _load_note_content(self):
        """Load note content from storage."""
        if 'filepath' in self.note_data and os.path.exists(self.note_data['filepath']):
            try:
                with open(self.note_data['filepath'], 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_input.text = content
                self.note_data['content'] = content
            except Exception as e:
                Logger.warning(f"Failed to load note content: {e}")
    
    def _minimize_note(self, instance):
        """Minimize the note to show only the header."""
        if self.is_minimized:
            # Already minimized, restore to original size
            self.height = self.original_height
            self.scroll_view.height = 250
            self.scroll_view.opacity = 1
            self.is_minimized = False
            instance.text = '_'
        else:
            # Store current height as original if not maximized
            if not self.is_maximized:
                self.original_height = self.height
            
            # Minimize: hide scroll view area
            self.height = self.minimized_height
            self.scroll_view.height = 0
            self.scroll_view.opacity = 0
            self.is_minimized = True
            self.is_maximized = False
            instance.text = '+'
            
            # Update maximize button
            for widget in self.children:
                if hasattr(widget, 'children'):
                    for child in widget.children:
                        if hasattr(child, 'children'):
                            for button in child.children:
                                if hasattr(button, 'text') and button.text in ['□', '◇']:
                                    button.text = '□'
    
    def _maximize_note(self, instance):
        """Maximize the note or restore to original size."""
        if self.is_maximized:
            # Restore to original size
            self.height = self.original_height
            self.scroll_view.height = 250
            self.scroll_view.opacity = 1
            self.is_maximized = False
            self.is_minimized = False
            instance.text = '□'
            
            # Update minimize button
            for widget in self.children:
                if hasattr(widget, 'children'):
                    for child in widget.children:
                        if hasattr(child, 'children'):
                            for button in child.children:
                                if hasattr(button, 'text') and button.text in ['_', '+']:
                                    button.text = '_'
        else:
            # Store current height as original if not minimized
            if not self.is_minimized:
                self.original_height = self.height
            
            # Maximize: make note take up more space
            container_height = 600  # Default max height
            if hasattr(self.app_instance, 'notes_scroll') and self.app_instance.notes_scroll.height > 0:
                container_height = self.app_instance.notes_scroll.height * 0.8
            
            max_height = max(400, min(container_height, 800))
            self.height = max_height
            self.scroll_view.height = max_height - 60  # Account for header
            self.scroll_view.opacity = 1
            self.is_maximized = True
            self.is_minimized = False
            instance.text = '◇'
            
            # Update minimize button
            for widget in self.children:
                if hasattr(widget, 'children'):
                    for child in widget.children:
                        if hasattr(child, 'children'):
                            for button in child.children:
                                if hasattr(button, 'text') and button.text in ['_', '+']:
                                    button.text = '_'
    
    def _save_note_data(self):
        """Save note metadata to storage."""
        self.app_instance.save_note_data(self.note_id, self.note_data)


class MobileNotedApp(App):
    """Main application class for Mobile Noted."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.notes: List[NoteCard] = []
        self.auto_save_enabled = True
        self.auto_save_interval = 10  # minutes
        self.spellcheck_enabled = SPELLCHECK_AVAILABLE  # Initialize spellcheck setting
        
        # Cloud storage configuration
        self.use_onedrive = False
        self.onedrive_path = None
        self.custom_storage_path = None
        
        # OneDrive Manager initialization for cloud sync
        self.onedrive_manager = None
        if ONEDRIVE_AVAILABLE:
            try:
                client_id = os.environ.get("NOTED_CLIENT_ID")
                if client_id:
                    self.onedrive_manager = OneDriveManager()
                    Logger.info("MobileNoted: OneDrive Manager initialized successfully")
                else:
                    Logger.info("MobileNoted: NOTED_CLIENT_ID not set, OneDrive sync disabled")
            except Exception as e:
                Logger.error(f"MobileNoted: Failed to initialize OneDrive Manager: {e}")
                self.onedrive_manager = None
        
        # Storage
        self.setup_storage()
        
        # Load configuration
        self.load_configuration()
    
    def setup_storage(self):
        """Setup storage directories and files with OneDrive support."""
        # Load basic configuration first to check storage preferences
        self._load_basic_config()
        
        # Determine primary storage location
        if self.use_onedrive and self.onedrive_path:
            # Use configured OneDrive path
            self.app_directory = os.path.join(self.onedrive_path, 'Documents', 'MobileNoted')
        elif self.custom_storage_path:
            # Use custom path
            self.app_directory = self.custom_storage_path
        else:
            # Use default platform-specific storage
            self.app_directory = self._get_default_storage_path()
        
        # Try OneDrive auto-detection if not configured
        if not self.use_onedrive and not self.custom_storage_path:
            detected_onedrive = self._detect_onedrive_path()
            if detected_onedrive:
                self.onedrive_path = detected_onedrive
                self.use_onedrive = True
                self.app_directory = os.path.join(detected_onedrive, 'Documents', 'MobileNoted')
        
        # Create directories
        try:
            os.makedirs(self.app_directory, exist_ok=True)
            self.notes_directory = os.path.join(self.app_directory, 'notes')
            os.makedirs(self.notes_directory, exist_ok=True)
        except (OSError, PermissionError) as e:
            Logger.warning(f"Failed to create primary storage directory: {e}")
            # Fallback to default local storage
            self._setup_fallback_storage()
        
        # Setup configuration storage
        self.config_file = os.path.join(self.app_directory, 'config.json')
        self.notes_db = JsonStore(os.path.join(self.app_directory, 'notes_db.json'))
        
    def _load_basic_config(self):
        """Load basic configuration to determine storage preferences."""
        # Try to load from default local location first
        default_storage = self._get_default_storage_path()
        default_config = os.path.join(default_storage, 'config.json')
        
        if os.path.exists(default_config):
            try:
                with open(default_config, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.use_onedrive = config.get('use_onedrive', False)
                self.onedrive_path = config.get('onedrive_path')
                self.custom_storage_path = config.get('custom_storage_path')
            except Exception as e:
                Logger.warning(f"Failed to load basic configuration: {e}")
    
    def _get_default_storage_path(self):
        """Get the default platform-specific storage path."""
        if platform == 'android':
            try:
                from android.storage import primary_external_storage_path
                storage_path = primary_external_storage_path()
                return os.path.join(storage_path, 'MobileNoted')
            except ImportError:
                # Fallback if android module not available
                return '/storage/emulated/0/MobileNoted'
        else:
            # Desktop or other platforms
            home_dir = os.path.expanduser('~')
            return os.path.join(home_dir, 'Documents', 'MobileNoted')
    
    def _detect_onedrive_path(self):
        """Try to detect OneDrive installation path."""
        if platform == 'android':
            # OneDrive detection not available on Android
            return None
            
        try:
            # Try environment variables (Windows/Mac)
            onedrive_paths = [
                os.environ.get("OneDriveCommercial"),  # OneDrive for Business
                os.environ.get("OneDrive"),            # Personal OneDrive
                os.environ.get("OneDriveConsumer"),    # Alternative personal OneDrive
            ]
            
            # Check each potential OneDrive path
            for onedrive_path in onedrive_paths:
                if onedrive_path and os.path.exists(onedrive_path):
                    # Test write access
                    test_dir = os.path.join(onedrive_path, "Documents", "MobileNoted")
                    try:
                        os.makedirs(test_dir, exist_ok=True)
                        test_file = os.path.join(test_dir, ".write_test")
                        with open(test_file, "w") as f:
                            f.write("test")
                        os.remove(test_file)
                        Logger.info(f"OneDrive detected at: {onedrive_path}")
                        return onedrive_path
                    except (OSError, PermissionError):
                        continue
            
            # Fallback: Try to detect from current script location
            current_dir = os.path.abspath(os.path.dirname(__file__))
            if "OneDrive" in current_dir:
                parts = current_dir.split(os.sep)
                for i, part in enumerate(parts):
                    if "OneDrive" in part:
                        onedrive_root = os.sep.join(parts[:i + 1])
                        if os.path.exists(onedrive_root):
                            Logger.info(f"OneDrive detected from path: {onedrive_root}")
                            return onedrive_root
                        break
                        
        except Exception as e:
            Logger.warning(f"OneDrive detection failed: {e}")
        
        return None
    
    def _setup_fallback_storage(self):
        """Setup fallback local storage if primary storage fails."""
        Logger.info("Setting up fallback local storage")
        self.app_directory = self._get_default_storage_path()
        self.use_onedrive = False
        self.onedrive_path = None
        
        try:
            os.makedirs(self.app_directory, exist_ok=True)
            self.notes_directory = os.path.join(self.app_directory, 'notes')
            os.makedirs(self.notes_directory, exist_ok=True)
        except Exception as e:
            Logger.error(f"Failed to create fallback storage: {e}")
            # Last resort: use temp directory
            import tempfile
            self.app_directory = os.path.join(tempfile.gettempdir(), 'MobileNoted')
            os.makedirs(self.app_directory, exist_ok=True)
            self.notes_directory = os.path.join(self.app_directory, 'notes')
            os.makedirs(self.notes_directory, exist_ok=True)
        
        # Setup configuration storage
        self.config_file = os.path.join(self.app_directory, 'config.json')
        self.notes_db = JsonStore(os.path.join(self.app_directory, 'notes_db.json'))
    
    def build(self):
        """Build the main application interface."""
        self.title = 'Mobile Noted'
        
        # Main layout
        main_layout = BoxLayout(orientation='vertical')
        
        # Header with app controls
        header = self.create_header()
        main_layout.add_widget(header)
        
        # Status bar for cloud/storage info
        status_bar = self.create_status_bar()
        main_layout.add_widget(status_bar)
        
        # Notes container
        self.notes_scroll = ScrollView()
        self.notes_container = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None)
        self.notes_container.bind(minimum_height=self.notes_container.setter('height'))
        
        self.notes_scroll.add_widget(self.notes_container)
        main_layout.add_widget(self.notes_scroll)
        
        # Load existing notes
        self.load_notes()
        
        # Start auto-save if enabled
        if self.auto_save_enabled:
            Clock.schedule_interval(self.auto_save_all, self.auto_save_interval * 60)
        
        return main_layout
    
    def create_header(self):
        """Create the application header with controls."""
        header_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=80)
        
        # Main buttons row
        buttons_row = GridLayout(cols=4, size_hint_y=None, height=50, spacing=5, padding=[5, 5, 5, 0])
        
        # Add Note button
        add_btn = Button(text='+ Note', size_hint_x=0.25)
        add_btn.bind(on_press=self.add_note)
        buttons_row.add_widget(add_btn)
        
        # Insert DateTime button
        datetime_btn = Button(text='Date/Time', size_hint_x=0.25)
        datetime_btn.bind(on_press=self.insert_datetime)
        buttons_row.add_widget(datetime_btn)
        
        # Equalize button
        equalize_btn = Button(text='Equalize', size_hint_x=0.25)
        equalize_btn.bind(on_press=self.equalize_windows)
        buttons_row.add_widget(equalize_btn)
        
        # Settings button
        settings_btn = Button(text='Settings', size_hint_x=0.25)
        settings_btn.bind(on_press=self.show_settings)
        buttons_row.add_widget(settings_btn)
        
        header_layout.add_widget(buttons_row)
        return header_layout
    
    def create_status_bar(self):
        """Create status bar showing storage and sync information."""
        self.status_bar = BoxLayout(orientation='horizontal', size_hint_y=None, height=30, padding=[5, 0, 5, 0])
        
        # Cloud status indicator
        self.cloud_status_label = Label(
            text=self._get_cloud_status_text(),
            size_hint_x=1.0,
            halign='center',
            text_size=(None, None)
        )
        self.status_bar.add_widget(self.cloud_status_label)
        
        return self.status_bar
    
    def _get_cloud_status_text(self):
        """Get the current cloud/storage status text."""
        if self.use_onedrive and self.onedrive_path:
            return "☁ OneDrive"
        elif self.custom_storage_path:
            return "📁 Custom"
        else:
            return "💾 Local"
    
    def update_status_bar(self):
        """Update the status bar with current information."""
        if hasattr(self, 'cloud_status_label'):
            self.cloud_status_label.text = self._get_cloud_status_text()
    
    def equalize_windows(self, instance):
        """Equalize the size of all note windows in the container."""
        if not self.notes:
            self.show_message("Equalize", "No notes to equalize.")
            return
        
        # Filter out minimized notes for height calculation
        non_minimized_notes = [note for note in self.notes if not note.is_minimized]
        
        if not non_minimized_notes:
            self.show_message("Equalize", "All notes are minimized. Nothing to equalize.")
            return
        
        # Calculate equal height for non-minimized notes
        container_height = self.notes_scroll.height
        if container_height <= 0:
            container_height = 600  # Default fallback height
        
        # Account for minimized notes (they take 60px each)
        minimized_count = len(self.notes) - len(non_minimized_notes)
        minimized_height_total = minimized_count * 60
        
        # Reserve space for spacing between all notes
        spacing_total = (len(self.notes) - 1) * 10 if len(self.notes) > 1 else 0
        available_height = container_height - spacing_total - minimized_height_total
        
        # Calculate equal height per non-minimized note (minimum 100px)
        equal_height = max(100, available_height // len(non_minimized_notes))
        
        # Apply equal height to non-minimized notes and reset their states
        for note in non_minimized_notes:
            note.height = equal_height
            note.text_input.height = equal_height - 60  # Account for header
            note.size_hint_y = None
            note.is_maximized = False
            note.original_height = equal_height
            
            # Update button states
            for widget in note.children:
                if hasattr(widget, 'children'):
                    for child in widget.children:
                        if hasattr(child, 'children'):
                            for button in child.children:
                                if hasattr(button, 'text'):
                                    if button.text in ['◇']:
                                        button.text = '□'  # Reset maximize button
        
        # Update container height (include all notes: minimized + non-minimized)
        total_height = (equal_height * len(non_minimized_notes)) + minimized_height_total + spacing_total
        self.notes_container.height = total_height
        
        self.show_message("Equalize", 
            f"Equalized {len(non_minimized_notes)} notes to {equal_height}px each.\n"
            f"{minimized_count} notes remain minimized.")
    
    def add_note(self, instance):
        """Add a new note."""
        note_data = {
            'id': str(uuid.uuid4()),
            'title': 'New Note',
            'content': '',
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat()
        }
        
        note_card = NoteCard(note_data, self)
        
        # Apply spellcheck setting to new note
        if hasattr(note_card, 'text_input') and hasattr(note_card.text_input, 'toggle_spell_check'):
            note_card.text_input.toggle_spell_check(self.spellcheck_enabled)
        
        self.notes.append(note_card)
        self.notes_container.add_widget(note_card)
        
        # Save note data
        self.save_note_data(note_data['id'], note_data)
    
    def delete_note(self, note_id: str):
        """Delete a note by ID."""
        # Find and remove from UI
        for note in self.notes[:]:
            if note.note_id == note_id:
                self.notes_container.remove_widget(note)
                self.notes.remove(note)
                break
        
        # Remove from storage
        if self.notes_db.exists(note_id):
            self.notes_db.delete(note_id)
    
    def insert_datetime(self, instance):
        """Insert current date/time into the active note."""
        if self.notes:
            # Get the last added note (most recent)
            last_note = self.notes[-1]
            current_text = last_note.text_input.text
            datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Insert at cursor position (append for now)
            if current_text:
                last_note.text_input.text = current_text + "\n" + datetime_str
            else:
                last_note.text_input.text = datetime_str
        else:
            self.show_message("No Notes", "Please add a note first.")
    
    def show_settings(self, instance):
        """Show settings dialog."""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Auto-save setting
        auto_save_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        auto_save_layout.add_widget(Label(text='Auto-save enabled:', size_hint_x=0.7))
        
        auto_save_switch = Switch(active=self.auto_save_enabled, size_hint_x=0.3)
        auto_save_layout.add_widget(auto_save_switch)
        content.add_widget(auto_save_layout)
        
        # Auto-save interval
        interval_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=80)
        interval_layout.add_widget(Label(text=f'Auto-save interval: {self.auto_save_interval} minutes', size_hint_y=None, height=30))
        
        interval_slider = Slider(min=1, max=60, value=self.auto_save_interval, step=1, size_hint_y=None, height=30)
        interval_layout.add_widget(interval_slider)
        content.add_widget(interval_layout)
        
        # Spellcheck setting
        spellcheck_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        spellcheck_available_text = 'Spellcheck enabled:' if SPELLCHECK_AVAILABLE else 'Spellcheck (unavailable):'
        spellcheck_layout.add_widget(Label(text=spellcheck_available_text, size_hint_x=0.7))
        
        spellcheck_switch = Switch(
            active=getattr(self, 'spellcheck_enabled', True) and SPELLCHECK_AVAILABLE, 
            size_hint_x=0.3,
            disabled=not SPELLCHECK_AVAILABLE
        )
        spellcheck_layout.add_widget(spellcheck_switch)
        content.add_widget(spellcheck_layout)
        
        # OneDrive Cloud Sync configuration
        # Cloud sync status
        cloud_status_text = "OneDrive: Not Connected"
        if self.onedrive_manager and self.onedrive_manager.is_authenticated():
            cloud_status_text = "OneDrive: Connected ✓"
        elif not ONEDRIVE_AVAILABLE:
            cloud_status_text = "OneDrive: Not Available"
            
        cloud_status_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
        cloud_status_layout.add_widget(Label(text=cloud_status_text, size_hint_x=0.7, color=(0, 1, 0, 1) if "Connected" in cloud_status_text else (1, 1, 1, 1)))
        
        # OneDrive auth button
        if ONEDRIVE_AVAILABLE:
            auth_text = "Logout" if (self.onedrive_manager and self.onedrive_manager.is_authenticated()) else "Connect"
            auth_button = Button(text=auth_text, size_hint_x=0.3, background_color=(0.8, 0.2, 0.2, 1) if auth_text == "Logout" else (0.2, 0.8, 0.2, 1))
            cloud_status_layout.add_widget(auth_button)
        
        content.add_widget(cloud_status_layout)
        
        # OneDrive sync buttons (only if available)
        if ONEDRIVE_AVAILABLE:
            sync_buttons_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)
            
            sync_now_button = Button(
                text='Sync Now',
                size_hint_x=0.5,
                background_color=(0.2, 0.2, 0.8, 1),
                disabled=not (self.onedrive_manager and self.onedrive_manager.is_authenticated())
            )
            
            load_cloud_button = Button(
                text='Load from Cloud',
                size_hint_x=0.5,
                background_color=(0.6, 0.2, 0.8, 1),
                disabled=not (self.onedrive_manager and self.onedrive_manager.is_authenticated())
            )
            
            sync_buttons_layout.add_widget(sync_now_button)
            sync_buttons_layout.add_widget(load_cloud_button)
            content.add_widget(sync_buttons_layout)
            
            # Bind OneDrive button events
            def handle_auth_button(instance):
                if self.onedrive_manager and self.onedrive_manager.is_authenticated():
                    # Logout
                    if self.onedrive_manager.logout():
                        auth_button.text = "Connect"
                        auth_button.background_color = (0.2, 0.8, 0.2, 1)
                        sync_now_button.disabled = True
                        load_cloud_button.disabled = True
                        cloud_status_layout.children[1].text = "OneDrive: Not Connected"
                        cloud_status_layout.children[1].color = (1, 1, 1, 1)
                else:
                    # Start authentication
                    popup.dismiss()
                    self.show_onedrive_auth(instance)
            
            def handle_sync_now(instance):
                popup.dismiss()
                self.sync_to_onedrive(instance)
            
            def handle_load_cloud(instance):
                popup.dismiss()
                self.load_from_onedrive(instance)
            
            if ONEDRIVE_AVAILABLE:
                auth_button.bind(on_press=handle_auth_button)
                sync_now_button.bind(on_press=handle_sync_now)
                load_cloud_button.bind(on_press=handle_load_cloud)

        # OneDrive configuration (only on non-Android platforms for local folder detection)
        if platform != 'android':
            # OneDrive enable/disable for local folder detection
            onedrive_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
            onedrive_layout.add_widget(Label(text='Use OneDrive local folder:', size_hint_x=0.7))
            
            onedrive_switch = Switch(active=self.use_onedrive, size_hint_x=0.3)
            onedrive_layout.add_widget(onedrive_switch)
            content.add_widget(onedrive_layout)
            
            # OneDrive path display
            onedrive_path_display = Label(
                text=f'OneDrive local path: {self.onedrive_path or "Not detected"}',
                size_hint_y=None,
                height=40,
                text_size=(None, None),
                halign='left'
            )
            content.add_widget(onedrive_path_display)
            
            # Custom storage path option
            custom_path_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)
            custom_path_layout.add_widget(Label(text='Custom storage path:', size_hint_x=0.5))
            
            custom_path_input = TextInput(
                text=self.custom_storage_path or '',
                multiline=False,
                size_hint_x=0.5
            )
            custom_path_layout.add_widget(custom_path_input)
            content.add_widget(custom_path_layout)
            
            # Storage configuration buttons
            storage_buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height=40, spacing=5)
            
            detect_onedrive_btn = Button(text='Detect OneDrive', size_hint_x=0.33)
            def detect_onedrive(instance):
                detected = self._detect_onedrive_path()
                if detected:
                    self.onedrive_path = detected
                    onedrive_path_display.text = f'OneDrive path: {detected}'
                    self.show_message("OneDrive", f"OneDrive detected at:\n{detected}")
                else:
                    self.show_message("OneDrive", "OneDrive not detected on this system")
            detect_onedrive_btn.bind(on_press=detect_onedrive)
            storage_buttons.add_widget(detect_onedrive_btn)
            
            reset_storage_btn = Button(text='Reset to Default', size_hint_x=0.33)
            def reset_storage(instance):
                self.use_onedrive = False
                self.onedrive_path = None
                self.custom_storage_path = None
                onedrive_switch.active = False
                custom_path_input.text = ""
                onedrive_path_display.text = "OneDrive path: Not detected"
                self.show_message("Storage", "Storage settings reset to default")
            reset_storage_btn.bind(on_press=reset_storage)
            storage_buttons.add_widget(reset_storage_btn)
            
            migrate_data_btn = Button(text='Migrate Data', size_hint_x=0.34)
            def migrate_data(instance):
                self._show_migration_dialog()
            migrate_data_btn.bind(on_press=migrate_data)
            storage_buttons.add_widget(migrate_data_btn)
            
            content.add_widget(storage_buttons)
        
        # Detailed storage information section
        storage_info_layout = BoxLayout(orientation='vertical', size_hint_y=None, height=120, spacing=5)
        
        # Storage type label
        storage_type = "Local Storage"
        if self.use_onedrive:
            storage_type = "OneDrive Cloud Storage"
        elif self.custom_storage_path:
            storage_type = "Custom Storage Location"
        
        storage_type_label = Label(
            text=f'Current Storage Type: {storage_type}',
            size_hint_y=None,
            height=25,
            halign='center',
            bold=True
        )
        storage_info_layout.add_widget(storage_type_label)
        
        # Storage location
        storage_location_label = Label(
            text=f'Location: {self.app_directory}',
            size_hint_y=None,
            height=25,
            halign='center',
            text_size=(None, None)
        )
        storage_info_layout.add_widget(storage_location_label)
        
        # Storage benefits/status
        storage_status = ""
        if self.use_onedrive:
            storage_status = "✓ Files synced to OneDrive • ✓ Available across devices • ✓ Automatic backup"
        elif self.custom_storage_path:
            storage_status = "• Files stored at custom location • Manual backup recommended"
        else:
            storage_status = "• Files stored locally only • Not synced to cloud • Enable OneDrive for sync"
        
        storage_status_label = Label(
            text=storage_status,
            size_hint_y=None,
            height=40,
            halign='center',
            text_size=(None, None)
        )
        storage_info_layout.add_widget(storage_status_label)
        
        # Cloud status indicator
        cloud_status_label = Label(
            text=f'Status: {self._get_cloud_status_text()}',
            size_hint_y=None,
            height=25,
            halign='center'
        )
        storage_info_layout.add_widget(cloud_status_label)
        
        content.add_widget(storage_info_layout)
        
        # Buttons
        buttons = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        
        def save_settings(instance):
            self.auto_save_enabled = auto_save_switch.active
            self.auto_save_interval = int(interval_slider.value)
            
            # Update spellcheck setting
            old_spellcheck = getattr(self, 'spellcheck_enabled', True)
            self.spellcheck_enabled = spellcheck_switch.active and SPELLCHECK_AVAILABLE
            
            # Apply spellcheck setting to all existing notes
            if old_spellcheck != self.spellcheck_enabled:
                for note_card in self.get_all_note_cards():
                    if hasattr(note_card, 'text_input') and hasattr(note_card.text_input, 'toggle_spell_check'):
                        note_card.text_input.toggle_spell_check(self.spellcheck_enabled)
            
            # Update OneDrive settings (only on non-Android)
            if platform != 'android':
                old_use_onedrive = self.use_onedrive
                old_custom_path = self.custom_storage_path
                
                self.use_onedrive = onedrive_switch.active
                custom_path = custom_path_input.text.strip()
                self.custom_storage_path = custom_path if custom_path else None
                
                # Check if storage location needs to change
                storage_changed = (
                    old_use_onedrive != self.use_onedrive or
                    old_custom_path != self.custom_storage_path
                )
                
                if storage_changed:
                    # Show restart message
                    self.show_message("Settings", 
                        "Storage settings saved!\n\n"
                        "Please restart the app for storage changes to take effect.\n\n"
                        "Use 'Migrate Data' to move existing notes to new location.")
            
            self.save_configuration()
            
            # Restart auto-save timer
            Clock.unschedule(self.auto_save_all)
            if self.auto_save_enabled:
                Clock.schedule_interval(self.auto_save_all, self.auto_save_interval * 60)
            
            popup.dismiss()
            if platform == 'android' or not storage_changed:
                self.show_message("Settings", "Settings saved successfully!")
        
        save_button = Button(text='Save')
        save_button.bind(on_press=save_settings)
        cancel_button = Button(text='Cancel')
        about_button = Button(text='About')
        about_button.bind(on_press=lambda x: self.show_about(x))
        
        buttons.add_widget(save_button)
        buttons.add_widget(cancel_button)
        buttons.add_widget(about_button)
        content.add_widget(buttons)
        
        popup = Popup(title='Settings', content=content, size_hint=(0.9, 0.8))
        cancel_button.bind(on_press=popup.dismiss)
        popup.open()
    
    def _show_migration_dialog(self):
        """Show data migration dialog."""
        content = BoxLayout(orientation='vertical', spacing=10, padding=10)
        
        # Instructions
        instructions = Label(
            text="Data Migration\n\n"
                 "This will copy all your notes and settings from the current "
                 "storage location to the new location based on your settings.\n\n"
                 "Current storage location:\n"
                 f"{self.app_directory}\n\n"
                 "Choose migration option:",
            text_size=(None, None),
            halign='center',
            size_hint_y=0.7
        )
        content.add_widget(instructions)
        
        # Migration options
        options_layout = BoxLayout(orientation='vertical', spacing=5, size_hint_y=0.3)
        
        copy_button = Button(text='Copy (Keep Original)', size_hint_y=None, height=40)
        move_button = Button(text='Move (Delete Original)', size_hint_y=None, height=40)
        cancel_button = Button(text='Cancel', size_hint_y=None, height=40)
        
        def perform_migration(is_move=False):
            try:
                # Determine new storage location
                new_storage = self._get_new_storage_path()
                if not new_storage or new_storage == self.app_directory:
                    self.show_message("Migration", "No new storage location configured or same as current.")
                    popup.dismiss()
                    return
                
                # Create new directory structure
                os.makedirs(new_storage, exist_ok=True)
                new_notes_dir = os.path.join(new_storage, 'notes')
                os.makedirs(new_notes_dir, exist_ok=True)
                
                # Copy/move files
                import shutil
                copied_files = 0
                
                # Copy configuration
                new_config_file = os.path.join(new_storage, 'config.json')
                if os.path.exists(self.config_file):
                    shutil.copy2(self.config_file, new_config_file)
                    copied_files += 1
                
                # Copy notes database
                new_notes_db = os.path.join(new_storage, 'notes_db.json')
                notes_db_file = os.path.join(self.app_directory, 'notes_db.json')
                if os.path.exists(notes_db_file):
                    shutil.copy2(notes_db_file, new_notes_db)
                    copied_files += 1
                
                # Copy notes directory
                if os.path.exists(self.notes_directory):
                    for filename in os.listdir(self.notes_directory):
                        src_file = os.path.join(self.notes_directory, filename)
                        dst_file = os.path.join(new_notes_dir, filename)
                        if os.path.isfile(src_file):
                            shutil.copy2(src_file, dst_file)
                            copied_files += 1
                
                # Remove original files if moving
                if is_move and copied_files > 0:
                    try:
                        if os.path.exists(self.config_file):
                            os.remove(self.config_file)
                        if os.path.exists(notes_db_file):
                            os.remove(notes_db_file)
                        if os.path.exists(self.notes_directory):
                            shutil.rmtree(self.notes_directory)
                        # Remove parent directory if empty
                        try:
                            os.rmdir(self.app_directory)
                        except OSError:
                            pass  # Directory not empty, that's ok
                    except Exception as e:
                        Logger.warning(f"Failed to remove some original files: {e}")
                
                action = "moved" if is_move else "copied"
                self.show_message("Migration", 
                    f"Successfully {action} {copied_files} files to:\n{new_storage}\n\n"
                    "Please restart the app to use the new location.")
                
            except Exception as e:
                Logger.error(f"Migration failed: {e}")
                self.show_message("Migration Error", f"Failed to migrate data:\n{str(e)}")
            
            popup.dismiss()
        
        copy_button.bind(on_press=lambda x: perform_migration(False))
        move_button.bind(on_press=lambda x: perform_migration(True))
        
        options_layout.add_widget(copy_button)
        options_layout.add_widget(move_button)
        options_layout.add_widget(cancel_button)
        content.add_widget(options_layout)
        
        popup = Popup(title='Data Migration', content=content, size_hint=(0.8, 0.6))
        cancel_button.bind(on_press=popup.dismiss)
        popup.open()
    
    def _get_new_storage_path(self):
        """Get the new storage path based on current settings."""
        if self.use_onedrive and self.onedrive_path:
            return os.path.join(self.onedrive_path, 'Documents', 'MobileNoted')
        elif self.custom_storage_path:
            return self.custom_storage_path
        else:
            return self._get_default_storage_path()
    
    def show_about(self, instance):
        """Show about dialog."""
        about_text = """Mobile Noted v1.0

A simple, mobile-friendly note-taking app with cloud storage.

Features:
• Multiple notes with auto-save
• Date/time insertion
• File save/load
• OneDrive cloud storage (desktop)
• Cross-platform synchronization
• Configurable storage locations
• Data migration tools

Converted from desktop Noted app."""
        
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=about_text, halign='center'))
        
        close_button = Button(text='Close', size_hint_y=None, height=50)
        content.add_widget(close_button)
        
        popup = Popup(title='About Mobile Noted', content=content, size_hint=(0.8, 0.6))
        close_button.bind(on_press=popup.dismiss)
        popup.open()
    
    def show_message(self, title: str, message: str):
        """Show a message popup."""
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text=message, halign='center'))
        
        close_button = Button(text='OK', size_hint_y=None, height=50)
        content.add_widget(close_button)
        
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.4))
        close_button.bind(on_press=popup.dismiss)
        popup.open()
    
    def load_notes(self):
        """Load notes from storage with OneDrive sync."""
        try:
            # First try to load from OneDrive if authenticated
            onedrive_loaded = False
            if self.onedrive_manager and self.onedrive_manager.is_authenticated():
                try:
                    onedrive_notes = self.onedrive_manager.list_notes()
                    if onedrive_notes:
                        Logger.info(f"Loading {len(onedrive_notes)} notes from OneDrive")
                        for note_info in onedrive_notes:
                            note_data = self.onedrive_manager.get_note(note_info["id"])
                            if note_data:
                                # Create note card with OneDrive ID
                                note_card = NoteCard(note_data, self)
                                setattr(note_card, 'onedrive_id', note_info["id"])
                                self.notes.append(note_card)
                                self.notes_container.add_widget(note_card)
                        onedrive_loaded = True
                except Exception as e:
                    Logger.warning(f"Failed to load from OneDrive: {e}")
            
            # Load from local storage if OneDrive not available or failed
            if not onedrive_loaded:
                Logger.info("Loading notes from local storage")
                for note_id in self.notes_db.keys():
                    note_data = self.notes_db.get(note_id)
                    if note_data:
                        note_card = NoteCard(note_data, self)
                        self.notes.append(note_card)
                        self.notes_container.add_widget(note_card)
                        
        except Exception as e:
            Logger.warning(f"Failed to load notes: {e}")
    
    def get_all_note_cards(self):
        """Get all note card widgets."""
        return [child for child in self.notes_container.children if isinstance(child, NoteCard)]
    
    def save_note_data(self, note_id: str, note_data: Dict[str, Any]):
        """Save note data to storage with OneDrive sync."""
        try:
            # Save to local storage first
            self.notes_db.put(note_id, **note_data)
            
            # Sync to OneDrive if authenticated and available
            if self.onedrive_manager and self.onedrive_manager.is_authenticated():
                try:
                    # Find the note card to get OneDrive ID
                    onedrive_id = None
                    for note in self.notes:
                        if getattr(note, 'note_id', None) == note_id:
                            onedrive_id = getattr(note, 'onedrive_id', None)
                            break
                    
                    # Save to OneDrive
                    saved_id = self.onedrive_manager.save_note(note_data, onedrive_id)
                    
                    # Update local note with OneDrive ID if new
                    if saved_id and not onedrive_id:
                        for note in self.notes:
                            if getattr(note, 'note_id', None) == note_id:
                                setattr(note, 'onedrive_id', saved_id)
                                break
                    
                except Exception as e:
                    Logger.warning(f"OneDrive sync failed during save: {e}")
                    # Continue with local save even if OneDrive fails
                    
        except Exception as e:
            Logger.warning(f"Failed to save note data: {e}")
    
    def auto_save_all(self, dt):
        """Auto-save all notes."""
        for note in self.notes:
            if note.text_input.text.strip():
                note._save_note_data()
    
    def load_configuration(self):
        """Load app configuration."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.auto_save_enabled = config.get('auto_save_enabled', True)
                self.auto_save_interval = config.get('auto_save_interval', 10)
                self.spellcheck_enabled = config.get('spellcheck_enabled', SPELLCHECK_AVAILABLE)
                self.use_onedrive = config.get('use_onedrive', self.use_onedrive)
                self.onedrive_path = config.get('onedrive_path', self.onedrive_path)
                self.custom_storage_path = config.get('custom_storage_path', self.custom_storage_path)
        except Exception as e:
            Logger.warning(f"Failed to load configuration: {e}")
    
    def save_configuration(self):
        """Save app configuration."""
        try:
            config = {
                'auto_save_enabled': self.auto_save_enabled,
                'auto_save_interval': self.auto_save_interval,
                'spellcheck_enabled': self.spellcheck_enabled,
                'use_onedrive': self.use_onedrive,
                'onedrive_path': self.onedrive_path,
                'custom_storage_path': self.custom_storage_path,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
                
            # Also save to default local location for bootstrapping
            if self.use_onedrive or self.custom_storage_path:
                self._save_config_to_default_location(config)
                
        except Exception as e:
            Logger.warning(f"Failed to save configuration: {e}")
    
    def _save_config_to_default_location(self, config):
        """Save configuration to default local location for bootstrapping."""
        try:
            default_storage = self._get_default_storage_path()
            os.makedirs(default_storage, exist_ok=True)
            default_config_file = os.path.join(default_storage, 'config.json')
            
            with open(default_config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            Logger.warning(f"Failed to save configuration to default location: {e}")
    
    def on_pause(self):
        """Handle app pause (Android)."""
        # Save all data when app is paused
        self.save_configuration()
        for note in self.notes:
            note._save_note_data()
        return True
    
    def on_resume(self):
        """Handle app resume (Android)."""
        pass

    # === OneDrive Cloud Sync Methods ===
    
    def show_onedrive_auth(self, instance):
        """Show OneDrive authentication dialog."""
        if not self.onedrive_manager:
            self._show_error_popup("OneDrive Not Available", "OneDrive integration is not available. Please check your configuration.")
            return
            
        if self.onedrive_manager.is_authenticated():
            self._show_onedrive_account_info()
        else:
            self._start_onedrive_authentication()
    
    def _start_onedrive_authentication(self):
        """Start the OneDrive authentication process."""
        try:
            user_code, verification_url, flow = self.onedrive_manager.start_device_flow_auth()
            
            if not user_code:
                self._show_error_popup("Authentication Error", "Failed to start OneDrive authentication. Please try again.")
                return
                
            # Create authentication popup
            content = BoxLayout(orientation='vertical', padding=20, spacing=15)
            
            # Instructions
            instructions = Label(
                text="To authenticate with OneDrive:",
                font_size='16sp',
                color=(1, 1, 1, 1),
                size_hint_y=None,
                height='40dp'
            )
            content.add_widget(instructions)
            
            # User code display
            code_label = Label(
                text=f"Device Code: [b]{user_code}[/b]",
                markup=True,
                font_size='20sp',
                color=(0.2, 0.8, 0.2, 1),
                size_hint_y=None,
                height='50dp'
            )
            content.add_widget(code_label)
            
            # URL display
            url_label = Label(
                text=f"Visit: {verification_url}",
                font_size='14sp',
                color=(0.5, 0.5, 1, 1),
                size_hint_y=None,
                height='40dp'
            )
            content.add_widget(url_label)
            
            # Status label
            status_label = Label(
                text="Waiting for authentication...",
                font_size='14sp',
                color=(1, 1, 0, 1),
                size_hint_y=None,
                height='40dp'
            )
            content.add_widget(status_label)
            
            # Buttons
            button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp', spacing=10)
            
            cancel_button = Button(
                text='Cancel',
                size_hint_x=0.5,
                background_color=(0.7, 0.3, 0.3, 1)
            )
            button_layout.add_widget(cancel_button)
            
            content.add_widget(button_layout)
            
            # Create popup
            popup = Popup(
                title='OneDrive Authentication',
                content=content,
                size_hint=(0.9, 0.7),
                auto_dismiss=False
            )
            
            # Complete authentication in background
            def complete_auth():
                auth_thread = self.onedrive_manager.complete_device_flow_auth(flow)
                
                # Monitor authentication
                def check_auth_status(dt):
                    if not auth_thread.is_alive():
                        # Authentication completed
                        if self.onedrive_manager.is_authenticated():
                            status_label.text = "Authentication successful! Syncing notes..."
                            status_label.color = (0, 1, 0, 1)
                            Clock.schedule_once(lambda dt: self._complete_onedrive_setup(popup), 2)
                        else:
                            status_label.text = "Authentication failed. Please try again."
                            status_label.color = (1, 0, 0, 1)
                        return False  # Stop checking
                    return True  # Continue checking
                
                Clock.schedule_interval(check_auth_status, 1.0)
            
            cancel_button.bind(on_press=popup.dismiss)
            
            popup.open()
            complete_auth()
            
        except Exception as e:
            Logger.error(f"OneDrive authentication error: {e}")
            self._show_error_popup("Authentication Error", f"Failed to authenticate with OneDrive: {str(e)}")
    
    def _complete_onedrive_setup(self, auth_popup):
        """Complete OneDrive setup after successful authentication."""
        auth_popup.dismiss()
        
        # Sync existing notes to OneDrive
        self.sync_to_onedrive()
        
        # Show success message
        self._show_info_popup("OneDrive Connected", "OneDrive authentication successful! Your notes will now be synced to the cloud.")
    
    def _show_onedrive_account_info(self):
        """Show OneDrive account information and logout option."""
        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        info_label = Label(
            text="OneDrive Account Connected",
            font_size='18sp',
            color=(0, 1, 0, 1),
            size_hint_y=None,
            height='50dp'
        )
        content.add_widget(info_label)
        
        # Buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height='50dp', spacing=10)
        
        sync_button = Button(
            text='Sync Now',
            size_hint_x=0.33,
            background_color=(0.2, 0.8, 0.2, 1)
        )
        
        logout_button = Button(
            text='Logout',
            size_hint_x=0.33,
            background_color=(0.8, 0.2, 0.2, 1)
        )
        
        close_button = Button(
            text='Close',
            size_hint_x=0.33,
            background_color=(0.5, 0.5, 0.5, 1)
        )
        
        button_layout.add_widget(sync_button)
        button_layout.add_widget(logout_button)
        button_layout.add_widget(close_button)
        content.add_widget(button_layout)
        
        popup = Popup(
            title='OneDrive Status',
            content=content,
            size_hint=(0.8, 0.4),
            auto_dismiss=False
        )
        
        def sync_now(instance):
            popup.dismiss()
            self.sync_to_onedrive()
        
        def logout_onedrive(instance):
            if self.onedrive_manager.logout():
                popup.dismiss()
                self._show_info_popup("OneDrive", "Logged out of OneDrive successfully.")
            else:
                self._show_error_popup("OneDrive", "Failed to logout of OneDrive.")
        
        sync_button.bind(on_press=sync_now)
        logout_button.bind(on_press=logout_onedrive)
        close_button.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def sync_to_onedrive(self, instance=None):
        """Sync all local notes to OneDrive."""
        if not self.onedrive_manager or not self.onedrive_manager.is_authenticated():
            self._show_error_popup("OneDrive Sync", "OneDrive is not connected. Please authenticate first.")
            return
        
        try:
            # Collect current notes data
            notes_data = {}
            for note in self.notes:
                note_id = getattr(note, 'note_id', str(uuid.uuid4()))
                notes_data[note_id] = {
                    "title": getattr(note, 'title', 'Untitled'),
                    "text": note.text_input.text,
                    "created": getattr(note, 'created_date', datetime.now().isoformat()),
                    "modified": datetime.now().isoformat(),
                    "note_id": note_id
                }
            
            # Perform sync
            synced_data = self.onedrive_manager.sync_local_notes(notes_data)
            
            # Update notes with OneDrive IDs
            for note_id, note_data in synced_data.items():
                for note in self.notes:
                    if getattr(note, 'note_id', None) == note_id:
                        if 'onedrive_id' in note_data:
                            note.onedrive_id = note_data['onedrive_id']
                        break
            
            self._show_info_popup("OneDrive Sync", f"Successfully synced {len(synced_data)} notes to OneDrive.")
            
        except Exception as e:
            Logger.error(f"OneDrive sync error: {e}")
            self._show_error_popup("OneDrive Sync Error", f"Failed to sync notes: {str(e)}")
    
    def load_from_onedrive(self, instance=None):
        """Load notes from OneDrive."""
        if not self.onedrive_manager or not self.onedrive_manager.is_authenticated():
            self._show_error_popup("OneDrive Load", "OneDrive is not connected. Please authenticate first.")
            return
        
        try:
            # Get OneDrive notes
            onedrive_notes = self.onedrive_manager.list_notes()
            
            if not onedrive_notes:
                self._show_info_popup("OneDrive Load", "No notes found in OneDrive.")
                return
            
            # Load each note
            loaded_count = 0
            for note_info in onedrive_notes:
                note_data = self.onedrive_manager.get_note(note_info["id"])
                if note_data:
                    # Create new note card
                    self.add_note_from_data(note_data, note_info["id"])
                    loaded_count += 1
            
            self._show_info_popup("OneDrive Load", f"Successfully loaded {loaded_count} notes from OneDrive.")
            
        except Exception as e:
            Logger.error(f"OneDrive load error: {e}")
            self._show_error_popup("OneDrive Load Error", f"Failed to load notes: {str(e)}")
    
    def add_note_from_data(self, note_data, onedrive_id=None):
        """Add a note card from data (used for OneDrive loading)."""
        note_card = NoteCard(app=self)
        
        # Set note data
        note_card.text_input.text = note_data.get("text", "")
        note_card.title = note_data.get("title", "Untitled")
        note_card.note_id = note_data.get("note_id", str(uuid.uuid4()))
        note_card.created_date = note_data.get("created", datetime.now().isoformat())
        
        if onedrive_id:
            note_card.onedrive_id = onedrive_id
        
        self.notes.append(note_card)
        self.notes_container.add_widget(note_card)
        
        return note_card
    
    def _show_info_popup(self, title, message):
        """Show information popup."""
        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        label = Label(
            text=message,
            text_size=(None, None),
            halign='center',
            valign='middle'
        )
        content.add_widget(label)
        
        ok_button = Button(
            text='OK',
            size_hint_y=None,
            height='50dp',
            background_color=(0.2, 0.8, 0.2, 1)
        )
        content.add_widget(ok_button)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.4)
        )
        
        ok_button.bind(on_press=popup.dismiss)
        popup.open()
    
    def _show_error_popup(self, title, message):
        """Show error popup."""
        content = BoxLayout(orientation='vertical', padding=20, spacing=15)
        
        label = Label(
            text=message,
            text_size=(None, None),
            halign='center',
            valign='middle',
            color=(1, 0.3, 0.3, 1)
        )
        content.add_widget(label)
        
        ok_button = Button(
            text='OK',
            size_hint_y=None,
            height='50dp',
            background_color=(0.8, 0.2, 0.2, 1)
        )
        content.add_widget(ok_button)
        
        popup = Popup(
            title=title,
            content=content,
            size_hint=(0.8, 0.4)
        )
        
        ok_button.bind(on_press=popup.dismiss)
        popup.open()


if __name__ == '__main__':
    MobileNotedApp().run()
