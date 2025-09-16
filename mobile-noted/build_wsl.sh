#!/bin/bash

# Build script for WSL2
set -e

echo "🚀 Building Mobile Noted for Android in WSL2..."

# Navigate to the project directory
cd "/mnt/c/Users/jwinn/OneDrive - Hayden Beverage/Documents/py/noted/mobile-noted"

# Create and activate virtual environment
echo "📦 Setting up virtual environment..."
python3 -m venv build_env
source build_env/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install buildozer and dependencies
echo "🔧 Installing buildozer..."
pip install buildozer cython

# Install project requirements
echo "📋 Installing project requirements..."
pip install -r requirements.txt

# Build the APK
echo "🏗️ Building Android APK..."
buildozer android debug

echo "✅ Build completed! APK should be in bin/ directory"
ls -la bin/