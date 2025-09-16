# Noted - Cross-Platform Note-Taking App

A versatile note-taking application available in both desktop and mobile versions.

## 📁 Project Structure

```
noted/
├── noted.py              # Desktop version (tkinter)
├── layout.json           # Desktop app layout persistence
├── mobile-noted/         # Mobile version for Android
│   ├── mobile-noted.py   # Main Kivy mobile app
│   ├── main.py          # Android entry point
│   ├── buildozer.spec   # Android build configuration
│   ├── build_android.*  # Build scripts for Android APK
│   └── README.md        # Mobile-specific documentation
└── .venv/               # Python virtual environment
```

## 🖥️ **Desktop Version** (`noted.py`)

Feature-rich desktop note-taking app with:
- Multiple note panes in a single window
- Window docking and positioning
- Real-time spell checking
- Auto-save functionality
- Session persistence (window position, open notes)
- OneDrive integration for cloud storage

### Quick Start:
```bash
python noted.py
```

## 📱 **Mobile Version** (`mobile-noted/`)

Android-compatible version built with Kivy:
- Touch-optimized interface
- Cloud storage integration
- File management with Android permissions
- Cross-platform synchronization
- APK build system ready

### Quick Start:
```bash
cd mobile-noted
python mobile-noted.py        # Test desktop version
./build_android.sh           # Build Android APK (Linux/WSL)
build_android.bat            # Build Android APK (Windows)
```

See [`mobile-noted/README.md`](mobile-noted/README.md) for detailed mobile setup.

## 🚀 **Features**

### Shared Features:
- ✅ Create, edit, and save notes
- ✅ Auto-save with configurable intervals  
- ✅ File import/export
- ✅ Settings persistence
- ✅ Date/time insertion
- ✅ Spell checking

### Desktop-Only Features:
- ✅ Window docking to screen edges
- ✅ Multi-monitor support
- ✅ Session restore (window position, open files)
- ✅ Advanced window management

### Mobile-Only Features:
- ✅ Touch-optimized interface
- ✅ Android storage permissions
- ✅ APK deployment ready
- ✅ Mobile file picker integration

## 📋 **Requirements**

### Desktop:
- Python 3.8+
- tkinter (usually included with Python)
- pyspellchecker (optional, for spell checking)

### Mobile/Android:
- Python 3.8+
- Kivy 2.0+
- Buildozer (for Android builds)
- Linux/WSL recommended for building

## 🔧 **Installation**

1. **Clone/Download** the project
2. **Create virtual environment** (recommended):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   # or
   .venv\Scripts\activate     # Windows
   ```
3. **Install dependencies**:
   ```bash
   pip install -r mobile-noted/requirements.txt
   ```

## 📖 **Documentation**

- [`mobile-noted/README.md`](mobile-noted/README.md) - Mobile app setup and features
- [`mobile-noted/ANDROID_DEPLOYMENT.md`](mobile-noted/ANDROID_DEPLOYMENT.md) - Android build guide
- [`mobile-noted/ONEDRIVE_FEATURES.md`](mobile-noted/ONEDRIVE_FEATURES.md) - Cloud integration

## 🎯 **Getting Started**

### Try Desktop Version:
```bash
python noted.py
```

### Try Mobile Version (Desktop):
```bash
cd mobile-noted
python mobile-noted.py
```

### Build for Android:
```bash
cd mobile-noted
./build_android.sh
```

---

**Choose your platform and start taking notes!** 📝
