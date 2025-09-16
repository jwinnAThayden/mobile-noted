# 📱 Mobile Noted - Android Version with OneDrive Cloud Storage

This directory contains the mobile-friendly version of the Noted app, converted from the desktop tkinter version to work on Android devices using the Kivy framework. Now includes comprehensive OneDrive cloud storage integration.

## 🚀 Quick Start - Download APK

### Latest Release (GitHub Actions Build)
The latest APK is built automatically using GitHub Actions:

1. Go to the [Actions](../../actions) tab
2. Click on the latest "Build Android APK" workflow run
3. Download the `mobile-noted-debug-apk` artifact
4. Extract the ZIP file to get the APK
5. Install on Android (enable "Unknown Sources")

### Manual Build Trigger
You can also trigger a new build manually:
1. Go to [Actions](../../actions) → "Build Android APK"
2. Click "Run workflow" → "Run workflow"
3. Wait 10-15 minutes for completion
4. Download from artifacts

## Files

- `main.py` - Main Kivy application for Android deployment with OneDrive support
- `test_desktop.py` - Desktop test version (run this to test the mobile app logic without Kivy)
- `requirements.txt` - Python dependencies
- `buildozer.spec` - Configuration for building Android APK
- `ONEDRIVE_FEATURES.md` - Comprehensive OneDrive integration documentation

## Features

### Core Features
- ✅ Multiple note cards in a scrollable interface
- ✅ Auto-save functionality with configurable intervals
- ✅ Date/time insertion
- ✅ File save/load operations
- ✅ Touch-friendly interface optimized for mobile
- ✅ Persistent storage across app sessions
- ✅ **Window equalization** for consistent note layout

### 🆕 Cloud Storage Features
- ✅ **OneDrive integration** with automatic detection
- ✅ **Cross-device synchronization** between desktop and mobile
- ✅ **Configurable storage locations** (OneDrive/Custom/Local)
- ✅ **Data migration tools** for moving between storage types
- ✅ **Cloud status indicators** in the UI
- ✅ **Automatic backup** to OneDrive
- ✅ **Offline access** with sync when online
- ✅ **Integrated storage management** in settings dialog

### Mobile Optimizations
- ✅ Touch-friendly button sizes and spacing
- ✅ Mobile-appropriate file storage locations
- ✅ Android storage permissions handling
- ✅ Portrait orientation optimized
- ✅ Responsive layout for different screen sizes

### Storage Options
- ✅ **OneDrive Cloud**: `OneDrive/Documents/MobileNoted/` (Recommended)
- ✅ **Custom Path**: User-defined directory location
- ✅ **Local Storage**: Platform-specific default locations
  - Android: `/storage/emulated/0/MobileNoted/`
  - Desktop: `~/Documents/MobileNoted/`
- ✅ Configuration stored in JSON format
- ✅ Notes metadata stored separately from content files

## Testing (Desktop)

To test the mobile app logic without installing Kivy:

```bash
cd mobile-noted
python test_desktop.py
```

This will open a desktop version that demonstrates all the mobile app functionality using tkinter.

## Development Setup

1. Install Kivy for desktop development:
```bash
pip install kivy[base] kivymd plyer
```

2. Test the Kivy version:
```bash
python main.py
```

## Android Build Setup

### Prerequisites
1. **Linux/WSL Recommended**: Android builds work best on Linux or WSL2
2. **Java 11**: Install OpenJDK 11 JDK
3. **Python 3.8+**: Ensure Python is installed
4. **System packages** (Linux/WSL):
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git zip unzip openjdk-11-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
```

### Quick Build Process

1. **Install Buildozer**:
```bash
pip3 install --user buildozer cython
```

2. **Build Debug APK** (Linux/WSL):
```bash
./build_android.sh
```

3. **Build Debug APK** (Windows):
```cmd
build_android.bat
```

4. **Build Release APK**:
```bash
./build_android.sh --release    # Linux/WSL
build_android.bat --release     # Windows
```

5. **Install on Device**:
```bash
./build_android.sh --install    # Linux/WSL
build_android.bat --install     # Windows
```

### Build Files
- `build_android.sh` - Linux/WSL build script
- `build_android.bat` - Windows build script  
- `buildozer.spec` - Android build configuration
- `main.py` - Android entry point
- See [`ANDROID_DEPLOYMENT.md`](ANDROID_DEPLOYMENT.md) for detailed guide

## Key Differences from Desktop Version

### Removed Features
- ❌ Window docking/positioning (not applicable on mobile)
- ❌ Multiple window management (replaced with single-screen cards)
- ❌ Windows-specific APIs (replaced with cross-platform alternatives)
- ❌ OneDrive integration (replaced with local/cloud-agnostic storage)

### Added Features
- ✅ Touch-optimized interface
- ✅ Mobile file picker integration
- ✅ Android storage permissions
- ✅ Mobile-friendly popups and dialogs
- ✅ Swipe-friendly scrolling

### Architecture Changes
- **UI Framework**: tkinter → Kivy
- **Layout**: Multiple windows → Single window with cards
- **Storage**: Windows paths → Platform-agnostic paths
- **File Access**: Direct file dialogs → Mobile-friendly pickers
- **Configuration**: Registry/Windows → JSON files

## App Structure

```
MobileNoted/
├── config.json          # App configuration
├── notes_db.json        # Notes metadata
└── notes/               # Individual note files
    ├── note1.txt
    ├── note2.txt
    └── ...
```

## Usage

1. **Add Note**: Tap the "+ Note" button to create a new note card
2. **Edit**: Tap in the text area to start typing
3. **Save File**: Tap "Save" to save the note as a text file
4. **Load File**: Tap "Load" to load an existing text file
5. **Insert Date/Time**: Tap "Date/Time" to insert current timestamp
6. **Settings**: Tap "Settings" to configure auto-save and other options
7. **Delete**: Tap "X" on a note card to delete it

## Building for Distribution

### Debug Build (for testing)
```bash
buildozer android debug
```
Creates: `bin/mobilenoted-1.0-debug.apk`

### Release Build (for Play Store)
```bash
buildozer android release
```
Creates: `bin/mobilenoted-1.0-release-unsigned.apk`

Then sign with your keystore for Play Store distribution.

## Android Permissions

The app requests these permissions:
- `WRITE_EXTERNAL_STORAGE` - Save notes to device storage
- `READ_EXTERNAL_STORAGE` - Load notes from device storage
- `INTERNET` - For future cloud sync features

## Future Enhancements

- [ ] Cloud sync integration (Google Drive, Dropbox)
- [ ] Rich text editing (bold, italic, lists)
- [ ] Note categories/tags
- [ ] Search functionality
- [ ] Dark mode theme
- [ ] Note sharing capabilities
- [ ] Widget for quick note access
- [ ] Voice-to-text integration
- [ ] Backup/restore functionality

## Troubleshooting

### Common Build Issues

1. **Java not found**: Install OpenJDK 8
2. **NDK/SDK issues**: Let Buildozer download them automatically
3. **Permission denied**: Check file permissions and paths
4. **Out of memory**: Increase build machine RAM or use cloud build

### Runtime Issues

1. **Storage permission denied**: Check Android permissions in Settings
2. **Files not saving**: Verify storage permissions and available space
3. **App crashes on startup**: Check logs with `adb logcat`

## Contributing

When contributing to the mobile version:

1. Test changes in `test_desktop.py` first
2. Ensure mobile-friendly UI design
3. Test on different screen sizes
4. Verify Android permissions work correctly
5. Update documentation for new features
# mobile-noted
