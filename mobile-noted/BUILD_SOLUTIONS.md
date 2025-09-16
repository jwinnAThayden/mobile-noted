# 🚀 Android Build Solutions for Mobile Noted

## ⚠️ Windows Build Issue

You encountered the "Unknown command/target android" error because **buildozer has significant limitations on Windows**. Here are your options:

## 🛠️ Solution Options (Recommended Order)

### 1. 🐳 **Docker Build (Recommended for Windows)**

The easiest solution for Windows users:

#### Prerequisites:
- Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop)

#### Build Steps:
```bash
# In the mobile-noted directory
.\build_docker.bat
```

This will:
- Build a Docker container with buildozer
- Compile your APK inside the Linux container
- Output the APK to the `bin/` directory

### 2. ☁️ **GitHub Actions (Cloud Build)**

Build your APK in the cloud using GitHub Actions:

#### Setup Steps:
1. Push your code to GitHub
2. The `.github/workflows/build-android.yml` workflow will automatically run
3. Download the built APK from the "Actions" tab > "Artifacts"

#### Manual Trigger:
- Go to your GitHub repository
- Click "Actions" tab
- Select "Build Android APK" workflow
- Click "Run workflow"

### 3. 🐧 **WSL2 (If Working)**

Your WSL2 setup had some issues, but you can try:

```bash
# In PowerShell
wsl -d kali-linux
cd /mnt/c/Users/jwinn/OneDrive\ -\ Hayden\ Beverage/Documents/py/noted/mobile-noted
./build_wsl.sh
```

### 4. 🖥️ **Test on Desktop First**

While setting up Android builds, test the app functionality on desktop:

```bash
cd mobile-noted
python mobile-noted.py
```

## 📱 **Expected Output**

After a successful build, you'll find:
- `bin/mobilenoted-1.0-debug.apk` - The Android application
- Build logs in `.buildozer/logs/`

## 🔧 **Installation on Android**

### Method 1: Direct Installation
1. Transfer the APK to your Android device
2. Enable "Unknown Sources" in Android settings
3. Tap the APK to install

### Method 2: ADB Installation (if you have ADB)
```bash
adb install bin/mobilenoted-1.0-debug.apk
```

## 📋 **Build Configuration**

The `buildozer.spec` file controls:
- App name: "Mobile Noted"
- Package: `com.haydenbeverage.mobilenoted`
- Target API: 31 (Android 12)
- Minimum API: 21 (Android 5.0)
- Permissions: Storage access, Internet

## 🎯 **Troubleshooting**

### Docker Issues:
- Ensure Docker Desktop is running
- Check that virtualization is enabled in BIOS
- Try `docker run hello-world` to test Docker

### WSL Issues:
- The `/etc/fstab` error is common and usually doesn't prevent builds
- Try updating WSL: `wsl --update`

### Build Failures:
- Check `.buildozer/logs/` for detailed error messages
- Try cleaning: `buildozer android clean` (in WSL/Docker)
- Ensure all dependencies are installed

## 🚀 **Quick Start**

**Fastest way to get your APK:**

1. **If you have Docker:** Run `.\build_docker.bat`
2. **If you have GitHub:** Push to GitHub and use Actions
3. **For testing:** Run `python mobile-noted.py` to test on desktop

The Docker method should work within 10-15 minutes on first build (includes downloading Android SDK/NDK).

## 📞 **Support**

If you encounter issues:
1. Check the specific error in build logs
2. Verify all prerequisites are installed
3. Try the alternative build methods

Each method has different advantages:
- **Docker**: Works on any system with Docker
- **GitHub Actions**: No local setup required
- **WSL2**: Best performance for repeated builds
- **Desktop testing**: Fastest for development iterations