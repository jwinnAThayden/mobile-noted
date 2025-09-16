#!/usr/bin/env python3
"""
Mobile Noted - Desktop Test Version
Test the mobile app logic without requiring Kivy installation
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import tkinter as tk
from tkinter import messagebox, filedialog, ttk


class MockNoteCard:
    """Mock note card for desktop testing."""
    
    def __init__(self, note_data: Dict[str, Any], app_instance):
        self.note_data = note_data
        self.app_instance = app_instance
        self.note_id = note_data.get('id', str(uuid.uuid4()))
        
        # Create a simple window for this note
        self.window = tk.Toplevel()
        self.window.title(note_data.get('title', 'New Note'))
        self.window.geometry("400x300")
        
        # Create UI
        self._create_ui()
        
        # Load content
        self._load_note_content()
    
    def _create_ui(self):
        """Create the note UI."""
        # Header frame
        header = tk.Frame(self.window)
        header.pack(fill=tk.X, padx=5, pady=5)
        
        # Title
        self.title_var = tk.StringVar(value=self.note_data.get('title', 'New Note'))
        title_entry = tk.Entry(header, textvariable=self.title_var)
        title_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        title_entry.bind('<KeyRelease>', self._on_title_change)
        
        # Control buttons
        tk.Button(header, text="Save", command=self._save_note).pack(side=tk.RIGHT, padx=2)
        tk.Button(header, text="Load", command=self._load_note).pack(side=tk.RIGHT, padx=2)
        tk.Button(header, text="X", command=self._delete_note).pack(side=tk.RIGHT, padx=2)
        
        # Text area
        text_frame = tk.Frame(self.window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.text_widget = tk.Text(text_frame, wrap=tk.WORD)
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.text_widget.yview)
        self.text_widget.configure(yscrollcommand=scrollbar.set)
        
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind text changes
        self.text_widget.bind('<KeyRelease>', self._on_text_change)
        self.text_widget.bind('<Button-1>', self._on_text_change)
        
        # Load initial content
        self.text_widget.insert('1.0', self.note_data.get('content', ''))
    
    def _on_title_change(self, event):
        """Handle title changes."""
        new_title = self.title_var.get()
        self.note_data['title'] = new_title
        self.window.title(new_title)
        self._save_note_data()
    
    def _on_text_change(self, event):
        """Handle text changes."""
        content = self.text_widget.get('1.0', tk.END).strip()
        self.note_data['content'] = content
        self.note_data['modified'] = datetime.now().isoformat()
        self._save_note_data()
    
    def _save_note(self):
        """Save note to file."""
        content = self.text_widget.get('1.0', tk.END).strip()
        if not content:
            messagebox.showerror("Error", "Cannot save empty note.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=self.app_instance.notes_directory,
            initialvalue=self.note_data.get('filename', f"note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                self.note_data['filename'] = os.path.basename(filename)
                self.note_data['filepath'] = filename
                self.note_data['title'] = os.path.basename(filename)
                self.title_var.set(self.note_data['title'])
                self.window.title(self.note_data['title'])
                self._save_note_data()
                
                messagebox.showinfo("Success", f"Note saved as {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save: {str(e)}")
    
    def _load_note(self):
        """Load note from file."""
        filename = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialdir=self.app_instance.notes_directory
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.text_widget.delete('1.0', tk.END)
                self.text_widget.insert('1.0', content)
                
                self.note_data['content'] = content
                self.note_data['filename'] = os.path.basename(filename)
                self.note_data['filepath'] = filename
                self.note_data['title'] = os.path.basename(filename)
                self.title_var.set(self.note_data['title'])
                self.window.title(self.note_data['title'])
                self._save_note_data()
                
                messagebox.showinfo("Success", f"Loaded {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load: {str(e)}")
    
    def _delete_note(self):
        """Delete this note."""
        if messagebox.askyesno("Delete Note", "Are you sure you want to delete this note?"):
            self.app_instance.delete_note(self.note_id)
            self.window.destroy()
    
    def _load_note_content(self):
        """Load note content from file if available."""
        if 'filepath' in self.note_data and os.path.exists(self.note_data['filepath']):
            try:
                with open(self.note_data['filepath'], 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_widget.delete('1.0', tk.END)
                self.text_widget.insert('1.0', content)
                self.note_data['content'] = content
            except Exception as e:
                print(f"Failed to load note content: {e}")
    
    def _save_note_data(self):
        """Save note metadata."""
        self.app_instance.save_note_data(self.note_id, self.note_data)


class MobileNotedTestApp:
    """Desktop test version of Mobile Noted app."""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Mobile Noted - Desktop Test")
        self.root.geometry("600x400")
        
        self.notes: List[MockNoteCard] = []
        self.auto_save_enabled = True
        self.auto_save_interval = 10  # minutes
        
        # Setup storage
        self.setup_storage()
        
        # Load configuration
        self.load_configuration()
        
        # Create UI
        self.create_ui()
        
        # Load existing notes
        self.load_notes()
    
    def setup_storage(self):
        """Setup storage directories and files."""
        home_dir = os.path.expanduser('~')
        self.app_directory = os.path.join(home_dir, 'Documents', 'MobileNotedTest')
        
        # Create directories
        os.makedirs(self.app_directory, exist_ok=True)
        self.notes_directory = os.path.join(self.app_directory, 'notes')
        os.makedirs(self.notes_directory, exist_ok=True)
        
        # Setup configuration storage
        self.config_file = os.path.join(self.app_directory, 'config.json')
        self.notes_db_file = os.path.join(self.app_directory, 'notes_db.json')
    
    def create_ui(self):
        """Create the main UI."""
        # Header frame
        header = tk.Frame(self.root)
        header.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(header, text="+ Add Note", command=self.add_note).pack(side=tk.LEFT, padx=5)
        tk.Button(header, text="Insert Date/Time", command=self.insert_datetime).pack(side=tk.LEFT, padx=5)
        tk.Button(header, text="Settings", command=self.show_settings).pack(side=tk.LEFT, padx=5)
        tk.Button(header, text="About", command=self.show_about).pack(side=tk.LEFT, padx=5)
        
        # Status frame
        status_frame = tk.Frame(self.root)
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.status_label = tk.Label(status_frame, text=f"Storage: {self.app_directory}")
        self.status_label.pack(side=tk.LEFT)
        
        # Notes list frame
        list_frame = tk.LabelFrame(self.root, text="Active Notes")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Listbox for notes
        self.notes_listbox = tk.Listbox(list_frame)
        list_scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.notes_listbox.yview)
        self.notes_listbox.configure(yscrollcommand=list_scrollbar.set)
        
        self.notes_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Double-click to focus note
        self.notes_listbox.bind('<Double-1>', self._focus_note)
    
    def add_note(self):
        """Add a new note."""
        note_data = {
            'id': str(uuid.uuid4()),
            'title': f'New Note {len(self.notes) + 1}',
            'content': '',
            'created': datetime.now().isoformat(),
            'modified': datetime.now().isoformat()
        }
        
        note_card = MockNoteCard(note_data, self)
        self.notes.append(note_card)
        self._update_notes_list()
        
        # Save note data
        self.save_note_data(note_data['id'], note_data)
    
    def delete_note(self, note_id: str):
        """Delete a note by ID."""
        # Find and remove from list
        for note in self.notes[:]:
            if note.note_id == note_id:
                self.notes.remove(note)
                break
        
        # Remove from storage
        try:
            notes_db = self._load_notes_db()
            if note_id in notes_db:
                del notes_db[note_id]
                self._save_notes_db(notes_db)
        except Exception as e:
            print(f"Failed to delete note from storage: {e}")
        
        self._update_notes_list()
    
    def insert_datetime(self):
        """Insert current date/time into the active note."""
        if self.notes:
            # Get the last focused note or the most recent
            last_note = self.notes[-1]
            current_text = last_note.text_widget.get('1.0', tk.END).strip()
            datetime_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Insert at the end
            if current_text:
                last_note.text_widget.insert(tk.END, "\n" + datetime_str)
            else:
                last_note.text_widget.insert('1.0', datetime_str)
            
            # Focus the note window
            last_note.window.lift()
            last_note.window.focus_force()
        else:
            messagebox.showinfo("No Notes", "Please add a note first.")
    
    def show_settings(self):
        """Show settings dialog."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.transient(self.root)
        
        # Auto-save setting
        auto_save_frame = tk.Frame(settings_window)
        auto_save_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.auto_save_var = tk.BooleanVar(value=self.auto_save_enabled)
        tk.Checkbutton(auto_save_frame, text="Enable auto-save", variable=self.auto_save_var).pack(anchor=tk.W)
        
        # Auto-save interval
        interval_frame = tk.Frame(settings_window)
        interval_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(interval_frame, text="Auto-save interval (minutes):").pack(anchor=tk.W)
        self.interval_var = tk.StringVar(value=str(self.auto_save_interval))
        tk.Entry(interval_frame, textvariable=self.interval_var, width=10).pack(anchor=tk.W, pady=5)
        
        # Storage location
        storage_frame = tk.LabelFrame(settings_window, text="Storage Location")
        storage_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(storage_frame, text=f"App Directory: {self.app_directory}", wraplength=350).pack(anchor=tk.W, padx=5, pady=5)
        tk.Label(storage_frame, text=f"Notes Directory: {self.notes_directory}", wraplength=350).pack(anchor=tk.W, padx=5, pady=5)
        
        # Buttons
        buttons_frame = tk.Frame(settings_window)
        buttons_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_settings():
            try:
                self.auto_save_enabled = self.auto_save_var.get()
                self.auto_save_interval = int(self.interval_var.get())
                self.save_configuration()
                messagebox.showinfo("Settings", "Settings saved successfully!")
                settings_window.destroy()
            except ValueError:
                messagebox.showerror("Error", "Please enter a valid number for the interval.")
        
        tk.Button(buttons_frame, text="Save", command=save_settings).pack(side=tk.LEFT, padx=5)
        tk.Button(buttons_frame, text="Cancel", command=settings_window.destroy).pack(side=tk.LEFT, padx=5)
    
    def show_about(self):
        """Show about dialog."""
        about_text = """Mobile Noted - Desktop Test v1.0

This is a desktop test version of the Mobile Noted app.

Features:
• Multiple note windows
• Auto-save functionality
• Date/time insertion
• File save/load
• Persistent storage

This version demonstrates the mobile app logic
using tkinter for desktop testing before 
converting to Kivy for Android deployment."""
        
        messagebox.showinfo("About Mobile Noted Test", about_text)
    
    def load_notes(self):
        """Load notes from storage."""
        try:
            notes_db = self._load_notes_db()
            for note_id, note_data in notes_db.items():
                note_card = MockNoteCard(note_data, self)
                self.notes.append(note_card)
            self._update_notes_list()
        except Exception as e:
            print(f"Failed to load notes: {e}")
    
    def save_note_data(self, note_id: str, note_data: Dict[str, Any]):
        """Save note data to storage."""
        try:
            notes_db = self._load_notes_db()
            notes_db[note_id] = note_data
            self._save_notes_db(notes_db)
        except Exception as e:
            print(f"Failed to save note data: {e}")
    
    def load_configuration(self):
        """Load app configuration."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.auto_save_enabled = config.get('auto_save_enabled', True)
                self.auto_save_interval = config.get('auto_save_interval', 10)
        except Exception as e:
            print(f"Failed to load configuration: {e}")
    
    def save_configuration(self):
        """Save app configuration."""
        try:
            config = {
                'auto_save_enabled': self.auto_save_enabled,
                'auto_save_interval': self.auto_save_interval,
                'last_updated': datetime.now().isoformat()
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Failed to save configuration: {e}")
    
    def _load_notes_db(self) -> Dict[str, Any]:
        """Load notes database."""
        if os.path.exists(self.notes_db_file):
            with open(self.notes_db_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_notes_db(self, notes_db: Dict[str, Any]):
        """Save notes database."""
        with open(self.notes_db_file, 'w', encoding='utf-8') as f:
            json.dump(notes_db, f, indent=2)
    
    def _update_notes_list(self):
        """Update the notes list display."""
        self.notes_listbox.delete(0, tk.END)
        for note in self.notes:
            title = note.note_data.get('title', 'Untitled')
            modified = note.note_data.get('modified', '')
            if modified:
                try:
                    mod_time = datetime.fromisoformat(modified).strftime('%m/%d %H:%M')
                    display_text = f"{title} ({mod_time})"
                except:
                    display_text = title
            else:
                display_text = title
            self.notes_listbox.insert(tk.END, display_text)
    
    def _focus_note(self, event):
        """Focus the selected note window."""
        selection = self.notes_listbox.curselection()
        if selection:
            index = selection[0]
            if index < len(self.notes):
                note = self.notes[index]
                note.window.lift()
                note.window.focus_force()
    
    def run(self):
        """Run the application."""
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        print(f"Mobile Noted Test started!")
        print(f"Storage directory: {self.app_directory}")
        print(f"Notes directory: {self.notes_directory}")
        
        self.root.mainloop()
    
    def _on_closing(self):
        """Handle application closing."""
        # Save all configurations and close note windows
        self.save_configuration()
        for note in self.notes[:]:
            note.window.destroy()
        self.root.destroy()


if __name__ == '__main__':
    app = MobileNotedTestApp()
    app.run()
