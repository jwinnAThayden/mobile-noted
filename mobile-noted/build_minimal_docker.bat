@echo off
REM Minimal Docker build that lets buildozer handle Android setup

echo 🐳 Building Mobile Noted with Minimal Docker Setup...

REM Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found. Install Docker Desktop.
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not running. Start Docker Desktop.
    exit /b 1
)

if not exist "buildozer.spec" (
    echo [ERROR] Run from mobile-noted directory
    exit /b 1
)

echo [INFO] Using minimal Docker approach - buildozer will handle Android SDK/NDK
echo [INFO] This is more reliable and should work consistently

REM Create output directory
if not exist "bin" mkdir bin

REM Build minimal image
echo [INFO] Building minimal Docker image...
docker build -f Dockerfile.minimal -t mobile-noted-minimal . --no-cache

if errorlevel 1 (
    echo [ERROR] Docker build failed!
    exit /b 1
)

echo [INFO] Running Android APK build...
echo [INFO] This will take 10-15 minutes as buildozer downloads Android tools
docker run --rm -v "%CD%\bin:/app/bin" mobile-noted-minimal

if errorlevel 1 (
    echo [ERROR] APK build failed!
    exit /b 1
)

echo [SUCCESS] Build completed! 🎉

if exist "bin\*.apk" (
    echo [INFO] APK files:
    dir /b bin\*.apk
    echo [INFO] Location: %CD%\bin\
    echo.
    echo [NEXT] Install APK on Android device:
    echo   1. Transfer APK to device
    echo   2. Enable "Unknown Sources"
    echo   3. Install APK
) else (
    echo [WARNING] No APK files found in bin\
)

pause