# Mobile Noted - OneDrive Cloud Storage Features

## Overview

Mobile Noted now includes comprehensive OneDrive cloud storage integration, allowing you to sync your notes across devices and maintain automatic backups. This feature provides seamless synchronization between desktop and mobile versions of the app.

## Features

### 🌟 **Automatic OneDrive Detection**
- The app automatically detects OneDrive installations on Windows and macOS
- Checks multiple OneDrive types: Personal OneDrive, OneDrive for Business
- Falls back gracefully to local storage if OneDrive is not available

### ☁️ **Cloud Storage Benefits**
- **Cross-device sync**: Access your notes from any device with OneDrive
- **Automatic backup**: Your notes are automatically backed up to the cloud
- **Version history**: OneDrive provides file version history
- **Offline access**: Notes remain available even when offline

### 🔧 **Configurable Storage Options**

#### 1. OneDrive Storage (Recommended)
- Automatically detected and configured
- Stores notes in `OneDrive/Documents/MobileNoted/`
- Provides seamless sync across all your devices
- Status indicator: `☁ OneDrive`

#### 2. Custom Storage Path
- Choose any directory on your system
- Useful for specific network drives or custom backup locations
- Full path control for advanced users
- Status indicator: `📁 Custom`

#### 3. Local Storage (Default)
- Stores notes locally on the device
- Platform-specific default locations:
  - **Android**: `/storage/emulated/0/MobileNoted/`
  - **Desktop**: `~/Documents/MobileNoted/`
- Status indicator: `💾 Local`

## User Interface

### Status Bar
The app includes a status bar below the main controls showing:
- **Cloud status indicator**: Shows current storage type (OneDrive/Custom/Local)
- **Storage Info button**: Click for detailed storage information

### Settings Dialog
Enhanced settings include:

#### OneDrive Configuration (Desktop only)
- **Use OneDrive storage**: Toggle switch to enable/disable OneDrive
- **OneDrive path display**: Shows detected OneDrive location
- **Custom storage path**: Text input for custom directory paths

#### Storage Management Buttons
- **Detect OneDrive**: Manually scan for OneDrive installations
- **Reset to Default**: Reset all storage settings to default local storage
- **Migrate Data**: Move notes between storage locations

## Data Migration

### Migration Options
When changing storage locations, you can:

1. **Copy (Keep Original)**
   - Copies all notes and settings to new location
   - Keeps original files as backup
   - Safe option for testing new storage

2. **Move (Delete Original)**
   - Moves all files to new location
   - Removes files from old location
   - Cleaner option when you're sure about the change

### What Gets Migrated
- Configuration files (`config.json`)
- Notes database (`notes_db.json`)
- All individual note files
- Directory structure preservation

## Technical Details

### Storage Structure
```
MobileNoted/
├── config.json          # App configuration
├── notes_db.json        # Notes metadata database
└── notes/               # Individual note files
    ├── note-1.txt
    ├── note-2.txt
    └── ...
```

### Configuration Persistence
- Configuration is saved in both primary and default local locations
- This ensures app can bootstrap storage settings on first run
- Graceful fallback if primary storage becomes unavailable

### Cross-Platform Compatibility
- **Windows**: Full OneDrive support with environment variable detection
- **macOS**: OneDrive support via environment variables
- **Android**: Local storage only (OneDrive app handles sync at OS level)
- **Linux**: Custom path support, no OneDrive auto-detection

## Setup Instructions

### First-Time Setup
1. **Launch the app** - OneDrive will be auto-detected if available
2. **Check status bar** - Verify storage type indicator
3. **Open Settings** - Configure storage preferences if needed
4. **Test sync** - Create a note and verify it appears in OneDrive

### Enabling OneDrive (if not auto-detected)
1. Open **Settings**
2. Click **"Detect OneDrive"** button
3. If detected, toggle **"Use OneDrive storage"** switch
4. Click **"Save"** and restart the app
5. Use **"Migrate Data"** to move existing notes

### Custom Storage Setup
1. Open **Settings**
2. Enter desired path in **"Custom storage path"** field
3. Toggle off **"Use OneDrive storage"** if enabled
4. Click **"Save"** and restart the app
5. Use **"Migrate Data"** to move existing notes

## Best Practices

### For OneDrive Users
- ✅ Keep OneDrive app running for continuous sync
- ✅ Ensure adequate OneDrive storage space
- ✅ Regularly check OneDrive sync status
- ✅ Use "Storage Info" to verify cloud status

### For Custom Storage Users
- ✅ Choose accessible, persistent locations
- ✅ Ensure write permissions for the app
- ✅ Set up manual backup routines
- ✅ Test path accessibility before migration

### For Local Storage Users
- ✅ Regularly backup notes manually
- ✅ Consider OneDrive upgrade for device sync
- ✅ Be aware notes won't sync across devices
- ✅ Use export features for sharing notes

## Troubleshooting

### OneDrive Not Detected
- **Check OneDrive installation**: Ensure OneDrive is installed and signed in
- **Verify environment variables**: OneDrive should set system environment variables
- **Manual path entry**: Use custom storage path with OneDrive folder path
- **Restart app**: Sometimes detection requires app restart

### Storage Access Issues
- **Check permissions**: Ensure app has write access to storage location
- **Verify path exists**: Custom paths must be valid and accessible
- **Fallback activation**: App will fallback to local storage if primary fails
- **Error logs**: Check console output for specific error messages

### Migration Problems
- **Free space**: Ensure destination has adequate free space
- **File conflicts**: Migration will overwrite existing files with same names
- **Partial migration**: If migration fails partway, some files may be duplicated
- **Recovery**: Original files remain unless "Move" option completes successfully

## Integration with Desktop Version

The mobile app shares the same storage structure and configuration as the desktop version, enabling:

- **Seamless switching**: Use desktop and mobile versions interchangeably
- **Shared configuration**: Settings sync between versions
- **Common file format**: Notes are compatible between desktop and mobile
- **Unified experience**: Same OneDrive integration across platforms

## Future Enhancements

Planned improvements include:
- Real-time sync indicators
- Conflict resolution for simultaneous edits
- Integration with other cloud providers (Google Drive, Dropbox)
- Enhanced Android OneDrive integration
- Automatic sync scheduling options

---

*For support or feature requests, please refer to the main application documentation or contact support.*
