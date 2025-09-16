@echo off
REM Build script for Mobile Noted Android app (Windows)

setlocal enabledelayedexpansion

echo 🚀 Building Mobile Noted for Android...

REM Check if we're in the right directory
if not exist "buildozer.spec" (
    echo [ERROR] buildozer.spec not found. Please run this script from the mobile-noted directory
    exit /b 1
)

if not exist "mobile-noted.py" (
    echo [ERROR] mobile-noted.py not found. Please run this script from the mobile-noted directory
    exit /b 1
)

REM Parse command line arguments
set BUILD_TYPE=debug
set INSTALL=false
set RUN=false
set CLEAN=false

:parse_args
if "%~1"=="" goto :done_parsing
if "%~1"=="-r" set BUILD_TYPE=release
if "%~1"=="--release" set BUILD_TYPE=release
if "%~1"=="-i" set INSTALL=true
if "%~1"=="--install" set INSTALL=true
if "%~1"=="--run" (
    set RUN=true
    set INSTALL=true
)
if "%~1"=="-c" set CLEAN=true
if "%~1"=="--clean" set CLEAN=true
if "%~1"=="-h" goto :show_help
if "%~1"=="--help" goto :show_help
shift
goto :parse_args

:show_help
echo Usage: %0 [OPTIONS]
echo Options:
echo   -r, --release    Build release version (default: debug)
echo   -i, --install    Install APK on connected device
echo   --run            Install and run APK on connected device
echo   -c, --clean      Clean build before building
echo   -h, --help       Show this help message
exit /b 0

:done_parsing

REM Check if buildozer is available
python -m buildozer --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Buildozer not found. Please install it with: pip install buildozer
    echo [WARNING] Buildozer on Windows has limitations. Consider using WSL for better results.
    exit /b 1
)

echo [WARNING] Note: Buildozer works best on Linux/WSL. Windows builds may have issues.
echo [INFO] For best results, use WSL2 with: wsl -d Ubuntu

REM Clean build if requested
if "%CLEAN%"=="true" (
    echo [INFO] Cleaning previous builds...
    python -m buildozer android clean
)

REM Check for Android device if install/run is requested
if "%INSTALL%"=="true" (
    adb devices >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] ADB not found. Building without device check...
        set INSTALL=false
        set RUN=false
    ) else (
        for /f "skip=1 tokens=*" %%i in ('adb devices') do (
            echo %%i | findstr "device$" >nul
            if not errorlevel 1 (
                echo [INFO] Android device found
                goto :device_found
            )
        )
        echo [WARNING] No Android devices connected. APK will be built but not installed.
        set INSTALL=false
        set RUN=false
    )
)

:device_found

REM Build the APK
echo [INFO] Building %BUILD_TYPE% APK...
echo [INFO] This may take a while on first build (downloading Android SDK/NDK)...

if "%BUILD_TYPE%"=="release" (
    if "%INSTALL%"=="true" (
        python -m buildozer android release install
    ) else (
        python -m buildozer android release
    )
) else (
    if "%INSTALL%"=="true" (
        if "%RUN%"=="true" (
            python -m buildozer android debug install run
        ) else (
            python -m buildozer android debug install
        )
    ) else (
        python -m buildozer android debug
    )
)

if errorlevel 1 (
    echo [ERROR] Build failed! Check .buildozer\logs\ for details
    exit /b 1
)

REM Report results
echo [INFO] Build completed successfully! 🎉

if exist "bin" (
    echo [INFO] APK files generated:
    for %%f in (bin\*.apk) do echo   - %%~nxf
    echo [INFO] APK location: %CD%\bin\
)

if "%INSTALL%"=="true" (
    if "%RUN%"=="false" (
        echo [INFO] App installed on device. Check your Android device to launch it.
    ) else (
        echo [INFO] App installed and launched on device.
    )
) else (
    echo [INFO] To install manually: Transfer APK to Android device and install
    echo [INFO] To install via ADB: Run this script with --install flag
)

echo.
echo [INFO] Build log available in: .buildozer\logs\

pause
