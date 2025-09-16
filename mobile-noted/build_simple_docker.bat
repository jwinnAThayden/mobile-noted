@echo off
REM Simple Docker build script using pre-built buildozer image

echo 🐳 Building Mobile Noted using Simple Docker Image...

REM Check if Docker is available and running
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found. Please install Docker Desktop.
    exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker daemon is not running. Please start Docker Desktop.
    exit /b 1
)

if not exist "buildozer.spec" (
    echo [ERROR] buildozer.spec not found. Please run from mobile-noted directory.
    exit /b 1
)

echo [INFO] Using lightweight pre-built buildozer image...
echo [INFO] This should be much faster than building from scratch.

REM Create bin directory
if not exist "bin" mkdir bin

REM Build using simple dockerfile
echo [INFO] Building Docker image...
docker build -f Dockerfile.simple -t mobile-noted-simple .

if errorlevel 1 (
    echo [ERROR] Docker image build failed!
    exit /b 1
)

echo [INFO] Running Android build...
docker run --rm -v "%CD%\bin:/app/bin" mobile-noted-simple

if errorlevel 1 (
    echo [ERROR] Android build failed!
    exit /b 1
)

echo [SUCCESS] Build completed! 🎉

if exist "bin\*.apk" (
    echo [INFO] APK files generated:
    dir /b bin\*.apk
    echo [INFO] Location: %CD%\bin\
) else (
    echo [WARNING] No APK files found
)

pause