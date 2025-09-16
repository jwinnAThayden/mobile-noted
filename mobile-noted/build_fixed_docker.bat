@echo off
REM Build script for Mobile Noted Android APK with compatibility fixes
REM This version addresses jnius compilation issues and uses stable package versions

echo.
echo =================================================
echo Building Mobile Noted Android APK - Fixed Version
echo =================================================
echo.

REM Clean up any existing containers
echo Cleaning up previous builds...
docker stop mobile-noted-fixed 2>nul
docker rm mobile-noted-fixed 2>nul

echo.
echo Building Docker image with compatibility fixes...
docker build -f Dockerfile.fixed -t mobile-noted-fixed .

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ Docker image build failed!
    pause
    exit /b 1
)

echo.
echo ✅ Docker image built successfully!
echo.
echo Starting APK build (this may take 15-30 minutes)...
echo The build will use Python 3.9 and compatible package versions.
echo.

REM Start the build in detached mode
docker run -d --name mobile-noted-fixed mobile-noted-fixed

if %ERRORLEVEL% neq 0 (
    echo.
    echo ❌ Failed to start build container!
    pause
    exit /b 1
)

echo ✅ Build container started successfully!
echo.
echo To monitor progress, run: docker logs -f mobile-noted-fixed
echo To check status, run: docker ps
echo.
echo The build process will:
echo 1. Download Android SDK tools
echo 2. Download Android NDK (~1GB)
echo 3. Compile Python for Android
echo 4. Build the APK
echo.
echo When complete, extract APK with: docker cp mobile-noted-fixed:/app/mobile-noted.apk .
echo.

pause