# Copilot Instructions for Noted Project

This document provides comprehensive guidance for AI coding agents working on the **Noted** cross-platform note-taking application.

## Project Overview

**Noted** is a dual-platform note-taking application with:
- **Desktop Version** (`noted.py`): Advanced Tkinter-based app with window management, multi-pane views, OneDrive integration
- **Mobile Version** (`mobile-noted/`): Kivy-based Android app with touch-optimized interface and cloud storage

## Architecture Patterns

### 1. **Dual Framework Architecture**
- **Desktop**: `tkinter` + `ttk` for enhanced styling
- **Mobile**: `kivy` framework with cross-platform compatibility
- **Shared Logic**: Common patterns for file I/O, configuration management, auto-save

### 2. **Configuration Management Pattern**
```python
# Both platforms use JSON-based configuration
config = {
    "auto_save_enabled": bool,
    "auto_save_interval": int,  # minutes
    "spellcheck_enabled": bool,
    "use_onedrive": bool,       # Desktop only
    "storage_path": str         # Platform-specific
}
```

### 3. **Cross-Platform Storage Strategy**
- **Desktop**: Prefers OneDrive for sync (`~/OneDrive/Documents/`)
- **Mobile**: Local storage with optional cloud sync
- **Fallback**: Platform-specific Documents folder
- **Configuration**: JSON files for persistence

## Development Workflows

### Desktop Development (`noted.py`)

#### **Class Structure**
```python
class EditableBoxApp:
    def __init__(self, root: tk.Tk)
    # Core UI Management
    def _create_ui()              # Main interface setup
    def _create_toolbar()         # Button/menu creation
    def _create_status_bar()      # Status information
    
    # View Management (Key Feature)
    def toggle_tabbed_view()      # Switch paned ↔ tabbed
    def _switch_to_tabbed_view()  # Enhanced notebook styling
    def _apply_custom_tab_colors() # Visual customization
    
    # File Operations
    def save_file(), load_file()  # Standard file I/O
    def _get_default_save_directory() # OneDrive-aware paths
    
    # Configuration & Persistence
    def _load_configuration()     # JSON config loading
    def _save_configuration()     # JSON config saving
    def _restore_boxes_from_layout() # Session persistence
    
    # Auto-Save System
    def start_auto_save()         # Threaded auto-save
    def configure_auto_save()     # Settings dialog
    
    # Window Management (Desktop-specific)
    def dock_move(direction)      # Screen positioning
    def minimize_app()            # Window state management
```

#### **Key Development Practices**
1. **Error Handling**: Always wrap file operations and UI updates in try/except blocks
2. **Configuration Persistence**: Use `_load_configuration()` and `_save_configuration()` for settings
3. **OneDrive Integration**: Check for OneDrive paths before fallback directories
4. **View State Management**: Support both paned and tabbed modes seamlessly
5. **Auto-Save**: Implement non-blocking, configurable auto-save with user control

### Mobile Development (`mobile-noted/`)

#### **Class Structure**
```python
class MobileNotedApp(App):
    # Core App Lifecycle
    def build()                   # Main UI construction
    def on_pause(), on_resume()   # Android lifecycle
    
    # Note Management
    def add_note(instance)        # Dynamic note creation
    def delete_note(note_id)      # Note removal with confirmation
    def get_all_note_cards()      # Widget collection
    
    # Storage & Persistence
    def load_notes()              # JSON-based note loading
    def save_note_data()          # Individual note persistence
    def auto_save_all()           # Batch auto-save
    
    # Cloud Storage (Advanced)
    def _get_new_storage_path()   # Storage location management
    def _show_migration_dialog()  # Data migration between storage types
    
    # UI Management
    def equalize_windows()        # Note layout normalization
    def show_settings()           # Configuration interface
    def update_status_bar()       # Dynamic status updates

class NoteCard(BoxLayout):
    # Individual note widget with:
    # - Text input with spellcheck
    # - File operations (save/load)
    # - Deletion controls
    # - Auto-save integration

class SpellCheckTextInput(TextInput):
    # Enhanced text input with live spellchecking
    # - Real-time error highlighting
    # - Word suggestion integration
    # - Performance optimization for large text
```

#### **Mobile-Specific Patterns**
1. **Touch Optimization**: Larger buttons, touch-friendly spacing
2. **Storage Management**: Platform-aware path handling (`android` vs desktop)
3. **Memory Efficiency**: Use generators for large note collections
4. **Lifecycle Awareness**: Handle Android pause/resume gracefully
5. **Cross-Platform Testing**: Use `test_desktop.py` for rapid development

## Code Conventions

### 1. **File Operations**
```python
# Always use try/except for file operations
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
except Exception as e:
    # Log error and provide fallback
    Logger.warning(f"Failed to load {file_path}: {e}")
    data = default_data
```

### 2. **Configuration Management**
```python
# Standard configuration pattern
def _load_configuration(self):
    """Load app configuration with defaults."""
    try:
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Apply loaded values with defaults
            self.auto_save_enabled = config.get('auto_save_enabled', True)
            self.auto_save_interval = config.get('auto_save_interval', 10)
    except Exception:
        # Set safe defaults on failure
        self.auto_save_enabled = True
        self.auto_save_interval = 10
```

### 3. **Cross-Platform Paths**
```python
# Desktop: OneDrive-aware path resolution
def _get_default_save_directory(self):
    """Get save directory, preferring OneDrive."""
    try:
        config_dir = os.path.dirname(self.config_file)
        if "OneDrive" in config_dir and os.path.exists(config_dir):
            return os.path.dirname(config_dir)  # Use Documents
        
        # Fallback to standard Documents
        if os.name == "nt":  # Windows
            docs = os.path.join(os.path.expanduser("~"), "Documents")
            if os.path.exists(docs):
                return docs
    except Exception:
        pass
    return os.path.abspath(os.path.dirname(__file__))

# Mobile: Platform-specific storage
def get_storage_path(self):
    """Get platform-appropriate storage path."""
    if platform == 'android':
        return '/storage/emulated/0/MobileNoted/'
    else:
        return os.path.join(os.path.expanduser('~'), 'Documents', 'MobileNoted')
```

### 4. **Auto-Save Implementation**
```python
# Desktop: Timer-based auto-save
def start_auto_save(self):
    """Start auto-save timer."""
    if self.auto_save_enabled and self.auto_save_interval > 0:
        if self.auto_save_job:
            self.root.after_cancel(self.auto_save_job)
        
        interval_ms = self.auto_save_interval * 60 * 1000
        self.auto_save_job = self.root.after(interval_ms, self.auto_save_and_reschedule)

# Mobile: Clock-based auto-save
def auto_save_all(self, dt):
    """Auto-save all notes periodically."""
    for note in self.notes:
        if note.text_input.text.strip():
            note._save_note_data()
```

## Testing Strategy

### **Desktop Testing**
```bash
# Direct execution
python noted.py

# Test auto-save functionality
# Test view switching (paned ↔ tabbed)
# Test OneDrive integration
# Test window docking and positioning
```

### **Mobile Testing**
```bash
# Desktop testing first (faster iteration)
cd mobile-noted
python test_desktop.py

# Kivy testing (after desktop validation)
python mobile-noted.py

# Android building and testing
./build_android.sh
```

### **Testing Priorities**
1. **Configuration persistence** across app restarts
2. **Auto-save functionality** with configurable intervals
3. **File operations** (save/load) with error handling
4. **View switching** without data loss (desktop)
5. **Cross-platform storage** path resolution

## Common Integration Points

### 1. **Shared Configuration Schema**
Both platforms use compatible JSON configuration with platform-specific extensions:
```json
{
  "auto_save_enabled": true,
  "auto_save_interval": 10,
  "spellcheck_enabled": true,
  "use_onedrive": true,          // Desktop only
  "storage_path": "/path/to/notes", // Platform-specific
  "last_updated": "2024-01-01T00:00:00"
}
```

### 2. **File Format Compatibility**
- **Note Files**: Plain text (.txt) for cross-platform compatibility
- **Configuration**: JSON for structured data
- **Layout Persistence**: JSON-based window/view state (desktop only)

### 3. **Cross-Platform Synchronization**
- **OneDrive Integration**: Desktop version syncs to cloud
- **Mobile Sync**: Can read OneDrive-stored configurations
- **Data Migration**: Tools for moving between storage locations

## Performance Considerations

### **Desktop Optimizations**
- **Lazy Loading**: Load layout and configuration on demand
- **Timer Management**: Cancel and reschedule auto-save timers properly
- **Memory Management**: Clean up widgets when switching views

### **Mobile Optimizations**
- **Touch Responsiveness**: Minimize blocking operations
- **Battery Efficiency**: Optimize auto-save frequency for mobile
- **Storage Efficiency**: Use JsonStore for lightweight data persistence

## Debugging Guidelines

### **Common Issues**
1. **Configuration Loading Failures**: Always provide default values
2. **File Path Issues**: Use `os.path.join()` and `os.path.exists()` consistently
3. **Auto-Save Conflicts**: Ensure proper timer cancellation before rescheduling
4. **View Switching Bugs**: Validate widget state before transitions
5. **Platform Detection**: Use proper platform checks (`os.name`, `kivy.utils.platform`)

### **Error Handling Patterns**
```python
# Standard error handling with logging
try:
    risky_operation()
except SpecificException as e:
    Logger.warning(f"Expected issue: {e}")
    apply_fallback_behavior()
except Exception as e:
    Logger.error(f"Unexpected error: {e}")
    show_user_friendly_message()
    use_safe_defaults()
```

## Development Best Practices

### **Code Organization**
1. **Single Responsibility**: Each method should have one clear purpose
2. **Configuration Centralization**: All settings managed through JSON config
3. **Error Resilience**: Graceful degradation when features fail
4. **Platform Abstraction**: Isolate platform-specific code in dedicated methods
5. **User Experience**: Always provide feedback for long-running operations

### **When Adding New Features**
1. **Desktop First**: Implement and test in `noted.py`
2. **Mobile Adaptation**: Port to `mobile-noted/mobile-noted.py`
3. **Configuration Support**: Add settings to JSON schema
4. **Cross-Platform Testing**: Validate on both platforms
5. **Documentation**: Update relevant README files

### **Integration Testing**
- Test configuration migration between versions
- Verify auto-save works across app restarts
- Validate file operations with various character encodings
- Check OneDrive sync behavior (desktop)
- Test Android lifecycle handling (mobile)

---

This guide should enable AI agents to contribute effectively to the Noted project while maintaining consistency across both desktop and mobile platforms.