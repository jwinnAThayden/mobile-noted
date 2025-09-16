# Android Deployment Guide for Mobile Noted

## Prerequisites

### 1. Install Dependencies on Linux/WSL (Recommended for Building)
Since Android builds work best on Linux, it's recommended to use WSL or a Linux machine:

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y git zip unzip openjdk-11-jdk python3-pip autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev

# Install Python dependencies
pip3 install --user buildozer cython
```

### 2. Android SDK/NDK Setup
Buildozer will automatically download and configure Android SDK and NDK, but you can speed up the process by pre-installing them.

## Build Process

### Option 1: Quick Build (Recommended)
1. Navigate to the mobile-noted directory:
   ```bash
   cd /path/to/mobile-noted
   ```

2. Initialize buildozer (first time only):
   ```bash
   buildozer android debug init
   ```

3. Build the APK:
   ```bash
   buildozer android debug
   ```

### Option 2: Release Build (For App Store)
1. Generate a signing key:
   ```bash
   keytool -genkey -v -keystore mobile-noted-release-key.keystore -alias mobile-noted -keyalg RSA -keysize 2048 -validity 10000
   ```

2. Build release APK:
   ```bash
   buildozer android release
   ```

3. Sign the APK:
   ```bash
   jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore mobile-noted-release-key.keystore bin/mobilenoted-*-release-unsigned.apk mobile-noted
   zipalign -v 4 bin/mobilenoted-*-release-unsigned.apk bin/mobile-noted-release.apk
   ```

## Build Configuration

The `buildozer.spec` file contains all build configuration:

- **Package Info**: Title, name, version, domain
- **Requirements**: Python packages needed (kivy, kivymd, plyer, pyenchant)
- **Permissions**: Storage access, internet (for future cloud sync)
- **Android API**: Targets API 31 (Android 12), minimum API 21 (Android 5.0)
- **Architecture**: ARM 32-bit and 64-bit support

## File Structure

```
mobile-noted/
├── main.py                 # Entry point for Android
├── mobile-noted.py         # Main application code
├── buildozer.spec         # Build configuration
├── requirements.txt       # Python dependencies
└── bin/                   # Generated APK files (after build)
```

## Installation on Android Device

### Debug Build (Development)
1. Enable "Developer Options" and "USB Debugging" on your Android device
2. Connect device via USB
3. Install the APK:
   ```bash
   buildozer android debug install run
   ```

### Release Build (Manual Installation)
1. Transfer the APK file to your Android device
2. Enable "Unknown Sources" in device settings
3. Tap the APK file to install

## Troubleshooting

### Common Issues:

1. **Build fails with Java errors**: Ensure you have OpenJDK 11 installed
2. **NDK/SDK download issues**: Check internet connection and try again
3. **Permission errors**: Make sure your user has write access to the build directory
4. **App crashes on Android**: Check logs with `adb logcat` while connected to device

### Build Logs:
Build logs are stored in `.buildozer/logs/` for debugging.

### Clean Build:
If builds fail, try cleaning:
```bash
buildozer android clean
```

## Features Working on Android

✅ Note creation and editing
✅ File save/load with Android storage permissions
✅ Spell checking (if pyenchant works on ARM)
✅ Settings persistence
✅ Touch-optimized UI
✅ Platform-specific storage paths
✅ Android permissions handling

## Future Enhancements

- Google Drive integration for cloud sync
- Share functionality with other Android apps
- Backup/restore via Android backup service
- Dark mode following system theme
