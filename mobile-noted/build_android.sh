#!/bin/bash
# Build script for Mobile Noted Android app

set -e  # Exit on any error

echo "🚀 Building Mobile Noted for Android..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "buildozer.spec" ] || [ ! -f "mobile-noted.py" ]; then
    print_error "Please run this script from the mobile-noted directory"
    exit 1
fi

# Check if buildozer is installed
if ! command -v buildozer &> /dev/null; then
    print_error "Buildozer not found. Please install it with: pip install buildozer"
    exit 1
fi

# Parse command line arguments
BUILD_TYPE="debug"
INSTALL=false
RUN=false
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--release)
            BUILD_TYPE="release"
            shift
            ;;
        -i|--install)
            INSTALL=true
            shift
            ;;
        --run)
            RUN=true
            INSTALL=true  # Must install before running
            shift
            ;;
        -c|--clean)
            CLEAN=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo "Options:"
            echo "  -r, --release    Build release version (default: debug)"
            echo "  -i, --install    Install APK on connected device"
            echo "  --run            Install and run APK on connected device"
            echo "  -c, --clean      Clean build before building"
            echo "  -h, --help       Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Clean build if requested
if [ "$CLEAN" = true ]; then
    print_status "Cleaning previous builds..."
    buildozer android clean
fi

# Check for Android device if install/run is requested
if [ "$INSTALL" = true ]; then
    if ! command -v adb &> /dev/null; then
        print_warning "ADB not found. Installing without device check..."
    else
        DEVICES=$(adb devices | grep -v "List of devices" | grep -c "device$" || true)
        if [ "$DEVICES" -eq 0 ]; then
            print_warning "No Android devices connected. APK will be built but not installed."
            INSTALL=false
            RUN=false
        else
            print_status "Found $DEVICES Android device(s) connected"
        fi
    fi
fi

# Build the APK
print_status "Building $BUILD_TYPE APK..."
print_status "This may take a while on first build (downloading Android SDK/NDK)..."

if [ "$BUILD_TYPE" = "release" ]; then
    if [ "$INSTALL" = true ]; then
        buildozer android release install
    else
        buildozer android release
    fi
else
    if [ "$INSTALL" = true ]; then
        if [ "$RUN" = true ]; then
            buildozer android debug install run
        else
            buildozer android debug install
        fi
    else
        buildozer android debug
    fi
fi

# Report results
print_status "Build completed successfully! 🎉"

if [ -d "bin" ]; then
    APK_COUNT=$(find bin -name "*.apk" | wc -l)
    if [ "$APK_COUNT" -gt 0 ]; then
        print_status "APK files generated:"
        find bin -name "*.apk" -exec basename {} \; | sed 's/^/  - /'
        print_status "APK location: $(pwd)/bin/"
    fi
fi

if [ "$INSTALL" = true ] && [ "$RUN" = false ]; then
    print_status "App installed on device. Check your Android device to launch it."
elif [ "$RUN" = true ]; then
    print_status "App installed and launched on device."
else
    print_status "To install manually: Transfer APK to Android device and install"
    print_status "To install via ADB: Run this script with --install flag"
fi

echo ""
print_status "Build log available in: .buildozer/logs/"
