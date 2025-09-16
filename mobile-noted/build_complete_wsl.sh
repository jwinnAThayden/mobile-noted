#!/bin/bash
# WSL2 Android build script with proper environment setup

set -e

echo "🚀 Starting Android build in WSL2..."
echo "📍 Current directory: $(pwd)"
echo "📋 Available space: $(df -h . | tail -1)"

# Check if buildozer is installed
if ! command -v buildozer &> /dev/null; then
    echo "📦 Installing buildozer..."
    pip3 install --user buildozer cython
    export PATH=$PATH:~/.local/bin
fi

# Check buildozer version
echo "📋 Buildozer version: $(buildozer --version)"

# Clean any previous build
if [ -d ".buildozer" ]; then
    echo "🧹 Cleaning previous build..."
    rm -rf .buildozer
fi

if [ -d "bin" ]; then
    echo "🧹 Cleaning previous APKs..."
    rm -rf bin
fi

# Set environment variables for Android SDK
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export ANDROID_SDK_ROOT=$HOME/.buildozer/android/platform/android-sdk

echo "🔧 Environment setup:"
echo "   JAVA_HOME: $JAVA_HOME"
echo "   ANDROID_SDK_ROOT: $ANDROID_SDK_ROOT"
echo "   PATH: $PATH"

# Start build
echo "🏗️ Starting buildozer android debug..."
buildozer android debug

echo "✅ Build completed!"

# Check results
if [ -d "bin" ] && [ -n "$(ls bin/*.apk 2>/dev/null)" ]; then
    echo "📱 APK files created:"
    ls -la bin/*.apk
    echo "🎉 Success! APK available at:"
    realpath bin/*.apk
else
    echo "❌ No APK files found"
    exit 1
fi