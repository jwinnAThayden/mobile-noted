#!/bin/bash

# Simple WSL2 build script for Mobile Noted
set -e

echo "🚀 Building Mobile Noted for Android in WSL2..."

# Navigate to the project directory
PROJECT_DIR="/mnt/c/Users/jwinn/OneDrive - Hayden Beverage/Documents/py/noted/mobile-noted"
cd "$PROJECT_DIR"

echo "📂 Current directory: $(pwd)"
echo "📋 Files present:"
ls -la

# Check if we have the required files
if [ ! -f "buildozer.spec" ]; then
    echo "❌ buildozer.spec not found!"
    exit 1
fi

if [ ! -f "mobile-noted.py" ]; then
    echo "❌ mobile-noted.py not found!"
    exit 1
fi

echo "✅ Required files found"

# Try to install buildozer with --break-system-packages if needed
echo "🔧 Installing buildozer..."
if ! python3 -c "import buildozer" 2>/dev/null; then
    echo "📦 Installing buildozer and dependencies..."
    pip3 install --user --break-system-packages buildozer cython || {
        echo "❌ Failed to install buildozer"
        echo "💡 Trying with virtual environment..."
        
        # Create virtual environment if pip install fails
        python3 -m venv build_venv
        source build_venv/bin/activate
        pip install --upgrade pip
        pip install buildozer cython
        pip install -r requirements.txt
    }
else
    echo "✅ buildozer already available"
fi

# Add local bin to PATH for cython and buildozer
export PATH="/home/jwinn/.local/bin:$PATH"

# Check buildozer installation
echo "🔍 Checking buildozer..."
if command -v buildozer >/dev/null 2>&1; then
    buildozer --version
elif python3 -c "import buildozer" 2>/dev/null; then
    python3 -m buildozer --version
else
    echo "❌ buildozer not found after installation"
    exit 1
fi

# Check cython installation
echo "🔍 Checking cython..."
if command -v cython >/dev/null 2>&1; then
    echo "✅ Cython found: $(cython --version)"
else
    echo "❌ Cython not in PATH, checking if available..."
    if [ -f "/home/jwinn/.local/bin/cython" ]; then
        echo "✅ Cython found at /home/jwinn/.local/bin/cython"
    else
        echo "❌ Cython not found"
        exit 1
    fi
fi

# Clean previous builds
echo "🧹 Cleaning previous builds..."
if [ -d ".buildozer" ]; then
    rm -rf .buildozer
fi
if [ -d "bin" ]; then
    rm -rf bin
fi

# Build the APK
echo "🏗️ Building Android APK..."
echo "⏰ This may take 10-15 minutes on first build..."

# Try buildozer command
if command -v buildozer >/dev/null 2>&1; then
    buildozer android debug
elif [ -f "build_venv/bin/activate" ]; then
    source build_venv/bin/activate
    buildozer android debug
else
    python3 -m buildozer android debug
fi

# Check if APK was created
echo "🔍 Checking for generated APK..."
if [ -d "bin" ] && [ -n "$(ls bin/*.apk 2>/dev/null)" ]; then
    echo "✅ Build completed successfully! 🎉"
    echo "📱 APK files generated:"
    ls -la bin/*.apk
    
    # Get file size and details
    for apk in bin/*.apk; do
        echo "📊 $apk:"
        echo "   Size: $(du -h "$apk" | cut -f1)"
        echo "   Type: $(file "$apk")"
    done
    
    echo ""
    echo "🎯 Next steps:"
    echo "1. Transfer APK to Android device"
    echo "2. Enable 'Unknown Sources' in Android settings"
    echo "3. Install the APK"
    
else
    echo "❌ No APK files found in bin/ directory"
    echo "📋 Build directory contents:"
    ls -la
    if [ -d ".buildozer/logs" ]; then
        echo "📜 Recent build logs:"
        find .buildozer/logs -name "*.log" -type f -printf '%T@ %p\n' | sort -n | tail -3 | cut -d' ' -f2-
    fi
    exit 1
fi