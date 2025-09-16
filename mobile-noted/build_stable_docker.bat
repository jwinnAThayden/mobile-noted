@echo off
REM Stable Docker build script for Mobile Noted Android APK

echo 🐳 Building Mobile Noted Android APK with Stable Docker Environment...
echo.

REM Check Docker availability
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found. Please install Docker Desktop.
    echo Download from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not running. Please start Docker Desktop and try again.
    pause
    exit /b 1
)

REM Verify we're in the correct directory
if not exist "buildozer.spec" (
    echo [ERROR] buildozer.spec not found. Please run from mobile-noted directory.
    pause
    exit /b 1
)

echo [INFO] Docker is available and running
echo [INFO] Using stable Docker build environment
echo [INFO] This build includes:
echo   - Ubuntu 22.04 base
echo   - Java 17 (Android SDK compatible)
echo   - Non-root user (avoids buildozer warnings)
echo   - Comprehensive error handling
echo   - 30-minute timeout protection
echo.

REM Create output directory
if not exist "bin" mkdir bin

echo [INFO] Building Docker image (this may take 5-10 minutes)...
docker build -f Dockerfile.stable -t mobile-noted-stable . --no-cache

if errorlevel 1 (
    echo [ERROR] Docker image build failed!
    echo [DEBUG] Check the output above for specific errors
    pause
    exit /b 1
)

echo [SUCCESS] Docker image built successfully!
echo.

echo [INFO] Starting Android APK build...
echo [INFO] This will take 10-15 minutes as buildozer downloads Android SDK/NDK
echo [INFO] Progress will be shown below:
echo.

REM Run the build with output volume
docker run --rm -v "%CD%\bin:/output" mobile-noted-stable

if errorlevel 1 (
    echo [ERROR] APK build failed!
    echo [DEBUG] Check the output above for specific errors
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Build process completed! 🎉
echo.

REM Check for APK files
if exist "bin\*.apk" (
    echo [SUCCESS] APK files found:
    dir /b bin\*.apk
    echo.
    echo [INFO] APK location: %CD%\bin\
    echo.
    echo [NEXT STEPS] To install APK on Android device:
    echo   1. Copy APK file to your Android device
    echo   2. Enable "Install from Unknown Sources" in Android settings
    echo   3. Open the APK file on your device to install
    echo   4. Grant any requested permissions
    echo.
    echo [SUCCESS] Mobile Noted Android app is ready! 📱
) else (
    echo [WARNING] No APK files found in bin\ directory
    echo [DEBUG] Checking if Docker volume mapping worked correctly...
    docker run --rm -v "%CD%\bin:/output" mobile-noted-stable ls -la bin/ 2>nul || echo "Could not check container bin directory"
)

echo.
pause