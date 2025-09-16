@echo off
REM Comprehensive Docker build script for Mobile Noted Android app

echo 🐳 Building Mobile Noted for Android using Docker (Complete Environment)...

REM Check if Docker is available
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found. Please install Docker Desktop for Windows.
    echo [INFO] Download from: https://www.docker.com/products/docker-desktop
    exit /b 1
)

REM Check if Docker daemon is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker daemon is not running. Please start Docker Desktop.
    exit /b 1
)

REM Check if we're in the right directory
if not exist "buildozer.spec" (
    echo [ERROR] buildozer.spec not found. Please run this script from the mobile-noted directory
    exit /b 1
)

echo [INFO] Setting up complete Android build environment in Docker...
echo [INFO] This includes Android SDK, NDK, Java, Python, and all build tools
echo [INFO] First build may take 15-20 minutes (downloading Android tools)

REM Clean up any existing containers and images
echo [INFO] Cleaning up previous Docker builds...
docker rmi mobile-noted-builder 2>nul
docker system prune -f >nul 2>&1

REM Build the Docker image with complete Android environment
echo [INFO] Building Docker image with Android SDK/NDK...
docker build -t mobile-noted-builder . --no-cache

if errorlevel 1 (
    echo [ERROR] Docker image build failed!
    echo [INFO] Check the error messages above for details
    exit /b 1
)

echo [INFO] Docker image built successfully!
echo [INFO] Starting Android APK build...

REM Create bin directory if it doesn't exist
if not exist "bin" mkdir bin

REM Run the build in Docker container
docker run --rm -v "%CD%\bin:/app/bin" mobile-noted-builder

if errorlevel 1 (
    echo [ERROR] Android build failed!
    echo [INFO] Check the build logs above for details
    exit /b 1
)

echo [INFO] Build completed! 🎉
echo [INFO] Checking for APK files...

if exist "bin\*.apk" (
    echo [SUCCESS] APK files generated:
    dir /b bin\*.apk
    echo.
    echo [INFO] APK location: %CD%\bin\
    echo [INFO] You can now install these APK files on your Android device
    echo.
    echo [NEXT STEPS]
    echo 1. Transfer APK to your Android device
    echo 2. Enable "Unknown Sources" in Android settings
    echo 3. Install the APK file
) else (
    echo [WARNING] No APK files found in bin directory
    echo [INFO] Build may have completed but APK wasn't copied correctly
    echo [INFO] Check the build logs above for details
)

echo.
echo [INFO] To rebuild: Run this script again
echo [INFO] To clean Docker: docker rmi mobile-noted-builder

pause