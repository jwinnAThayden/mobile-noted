#!/usr/bin/env python3
"""
Simple Mobile Noted - Minimal version for Android build testing
Cross-platform note-taking app - simplified for reliable builds
"""

import os
import json
import logging
from datetime import datetime

import kivy
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.switch import Switch
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.utils import platform
from kivy.logger import Logger

# Require minimum Kivy version
kivy.require('2.0.0')

class SimpleNoteCard(BoxLayout):
    """Simplified note card without spell checking"""
    
    def __init__(self, note_id=None, app_instance=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 300
        self.spacing = 5
        self.padding = [10, 5, 10, 5]
        
        self.note_id = note_id or f"note_{datetime.now().timestamp()}"
        self.app_instance = app_instance
        
        # Note text input (simplified without spell checking)
        self.text_input = TextInput(
            multiline=True,
            size_hint_y=0.8,
            hint_text="Start typing your note here...",
            font_size='16sp'
        )
        self.text_input.bind(text=self._on_text_change)
        
        # Control buttons
        button_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2, spacing=5)
        
        save_btn = Button(text='Save', size_hint_x=0.3)
        save_btn.bind(on_press=self._save_note)
        
        delete_btn = Button(text='Delete', size_hint_x=0.3)
        delete_btn.bind(on_press=self._confirm_delete)
        
        button_layout.add_widget(save_btn)
        button_layout.add_widget(Label(size_hint_x=0.4))  # Spacer
        button_layout.add_widget(delete_btn)
        
        self.add_widget(self.text_input)
        self.add_widget(button_layout)
        
        # Load existing note data
        self._load_note_data()
    
    def _on_text_change(self, instance, value):
        """Handle text changes"""
        if self.app_instance and hasattr(self.app_instance, 'mark_unsaved_changes'):
            self.app_instance.mark_unsaved_changes()
    
    def _save_note(self, instance):
        """Save note to storage"""
        try:
            note_data = {
                'id': self.note_id,
                'text': self.text_input.text,
                'created': datetime.now().isoformat(),
                'modified': datetime.now().isoformat()
            }
            
            if self.app_instance:
                self.app_instance.save_note_data(self.note_id, note_data)
                Logger.info(f"SimpleMobileNoted: Saved note {self.note_id}")
        except Exception as e:
            Logger.error(f"SimpleMobileNoted: Error saving note: {e}")
    
    def _load_note_data(self):
        """Load note from storage"""
        try:
            if self.app_instance:
                note_data = self.app_instance.load_note_data(self.note_id)
                if note_data and 'text' in note_data:
                    self.text_input.text = note_data['text']
                    Logger.info(f"SimpleMobileNoted: Loaded note {self.note_id}")
        except Exception as e:
            Logger.error(f"SimpleMobileNoted: Error loading note: {e}")
    
    def _confirm_delete(self, instance):
        """Show delete confirmation"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=f'Delete this note?\n\nThis action cannot be undone.', 
                                text_size=(250, None), halign='center'))
        
        button_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)
        
        cancel_btn = Button(text='Cancel', size_hint_x=0.5)
        delete_btn = Button(text='Delete', size_hint_x=0.5)
        
        button_layout.add_widget(cancel_btn)
        button_layout.add_widget(delete_btn)
        content.add_widget(button_layout)
        
        popup = Popup(title='Confirm Delete', content=content, size_hint=(0.8, 0.4))
        
        cancel_btn.bind(on_press=popup.dismiss)
        delete_btn.bind(on_press=lambda x: self._delete_note(popup))
        
        popup.open()
    
    def _delete_note(self, popup):
        """Actually delete the note"""
        popup.dismiss()
        if self.app_instance:
            self.app_instance.delete_note(self.note_id)


class SimpleMobileNotedApp(App):
    """Simplified Mobile Noted App for reliable Android builds"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.notes = []
        self.auto_save_enabled = True
        self.auto_save_interval = 300  # 5 minutes
        self.storage_path = self.get_storage_path()
        self.notes_store = None
        
        # Ensure storage directory exists
        try:
            os.makedirs(self.storage_path, exist_ok=True)
            Logger.info(f"SimpleMobileNoted: Storage path: {self.storage_path}")
        except Exception as e:
            Logger.error(f"SimpleMobileNoted: Error creating storage path: {e}")
    
    def get_storage_path(self):
        """Get platform-appropriate storage path"""
        if platform == 'android':
            try:
                # Try to use Android external storage
                from android.storage import primary_external_storage_path
                return os.path.join(primary_external_storage_path(), 'SimpleMobileNoted')
            except:
                return '/storage/emulated/0/SimpleMobileNoted/'
        else:
            # Desktop/other platforms
            return os.path.join(os.path.expanduser('~'), 'Documents', 'SimpleMobileNoted')
    
    def build(self):
        """Build the main UI"""
        Logger.info("SimpleMobileNoted: Building app...")
        
        # Initialize storage
        try:
            store_path = os.path.join(self.storage_path, 'notes.json')
            self.notes_store = JsonStore(store_path)
        except Exception as e:
            Logger.error(f"SimpleMobileNoted: Error initializing storage: {e}")
        
        # Main layout
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Header
        header = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        title_label = Label(text='Simple Mobile Noted', font_size='20sp', size_hint_x=0.7)
        add_btn = Button(text='+ Add Note', size_hint_x=0.3)
        add_btn.bind(on_press=self.add_note)
        
        header.add_widget(title_label)
        header.add_widget(add_btn)
        
        # Notes scroll area
        scroll = ScrollView()
        self.notes_layout = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=[0, 10])
        self.notes_layout.bind(minimum_height=self.notes_layout.setter('height'))
        
        scroll.add_widget(self.notes_layout)
        
        main_layout.add_widget(header)
        main_layout.add_widget(scroll)
        
        # Load existing notes
        self.load_notes()
        
        # Start auto-save
        if self.auto_save_enabled:
            Clock.schedule_interval(self.auto_save_all, self.auto_save_interval)
        
        Logger.info("SimpleMobileNoted: App built successfully")
        return main_layout
    
    def add_note(self, instance):
        """Add a new note"""
        try:
            note_card = SimpleNoteCard(app_instance=self)
            self.notes.append(note_card)
            self.notes_layout.add_widget(note_card)
            Logger.info("SimpleMobileNoted: Added new note")
        except Exception as e:
            Logger.error(f"SimpleMobileNoted: Error adding note: {e}")
    
    def delete_note(self, note_id):
        """Delete a note"""
        try:
            # Remove from storage
            if self.notes_store and self.notes_store.exists(note_id):
                self.notes_store.delete(note_id)
            
            # Remove from UI
            for note in self.notes[:]:  # Copy list for safe iteration
                if hasattr(note, 'note_id') and note.note_id == note_id:
                    self.notes_layout.remove_widget(note)
                    self.notes.remove(note)
                    break
            
            Logger.info(f"SimpleMobileNoted: Deleted note {note_id}")
        except Exception as e:
            Logger.error(f"SimpleMobileNoted: Error deleting note: {e}")
    
    def save_note_data(self, note_id, note_data):
        """Save note data to storage"""
        try:
            if self.notes_store:
                self.notes_store.put(note_id, **note_data)
        except Exception as e:
            Logger.error(f"SimpleMobileNoted: Error saving note data: {e}")
    
    def load_note_data(self, note_id):
        """Load note data from storage"""
        try:
            if self.notes_store and self.notes_store.exists(note_id):
                return dict(self.notes_store.get(note_id))
        except Exception as e:
            Logger.error(f"SimpleMobileNoted: Error loading note data: {e}")
        return None
    
    def load_notes(self):
        """Load all existing notes"""
        try:
            if self.notes_store:
                for note_id in self.notes_store.keys():
                    note_card = SimpleNoteCard(note_id=note_id, app_instance=self)
                    self.notes.append(note_card)
                    self.notes_layout.add_widget(note_card)
                Logger.info(f"SimpleMobileNoted: Loaded {len(self.notes)} notes")
        except Exception as e:
            Logger.error(f"SimpleMobileNoted: Error loading notes: {e}")
    
    def auto_save_all(self, dt):
        """Auto-save all notes"""
        try:
            for note in self.notes:
                if hasattr(note, '_save_note'):
                    note._save_note(None)
            Logger.info("SimpleMobileNoted: Auto-save completed")
        except Exception as e:
            Logger.error(f"SimpleMobileNoted: Error in auto-save: {e}")
    
    def mark_unsaved_changes(self):
        """Mark that there are unsaved changes"""
        # Could be used for future features
        pass
    
    def on_pause(self):
        """Handle app pause (Android lifecycle)"""
        Logger.info("SimpleMobileNoted: App paused")
        self.auto_save_all(None)
        return True
    
    def on_resume(self):
        """Handle app resume (Android lifecycle)"""
        Logger.info("SimpleMobileNoted: App resumed")


if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    try:
        app = SimpleMobileNotedApp()
        app.run()
    except Exception as e:
        Logger.error(f"SimpleMobileNoted: Fatal error: {e}")
        print(f"Error starting app: {e}")