#!/bin/bash

# Comprehensive pyjnius patcher for all build directories
# Run this in your Linux VM at: /home/jwinn/Documents/noted/mobile-noted

echo "=== Comprehensive pyjnius Python 3 Compatibility Patcher ==="
echo "Current directory: $(pwd)"

# Step 1: Find and patch ALL jnius_utils.pxi files in the entire build tree
echo -e "\n=== Finding and patching ALL jnius_utils.pxi files ==="

# Find all jnius_utils.pxi files
find . -name "jnius_utils.pxi" -type f 2>/dev/null | while read -r file; do
    echo "Processing: $file"
    
    # Add compatibility alias at top if not present
    if ! grep -q "long = int" "$file"; then
        echo "  Adding long = int compatibility alias"
        sed -i '1i try:\n    long\nexcept NameError:\n    long = int\n' "$file"
    fi
    
    # Replace all isinstance(arg, long) with isinstance(arg, int)
    if grep -q "isinstance(arg, long)" "$file"; then
        echo "  Replacing isinstance(arg, long) with isinstance(arg, int)"
        sed -i 's/isinstance(arg, long)/isinstance(arg, int)/g' "$file"
    fi
done

# Step 2: Also patch the python-for-android recipe source
echo -e "\n=== Patching python-for-android recipe source ==="
RECIPE_PATH=".buildozer/android/platform/python-for-android/pythonforandroid/recipes/pyjnius"
if [ -d "$RECIPE_PATH" ]; then
    find "$RECIPE_PATH" -name "*.pxi" -o -name "*.py" -o -name "*.pyx" | while read -r file; do
        if grep -q "isinstance(arg, long)" "$file" 2>/dev/null; then
            echo "Patching recipe file: $file"
            # Add alias if not present
            if ! grep -q "long = int" "$file"; then
                sed -i '1i try:\n    long\nexcept NameError:\n    long = int\n' "$file"
            fi
            # Replace occurrences
            sed -i 's/isinstance(arg, long)/isinstance(arg, int)/g' "$file"
        fi
    done
fi

# Step 3: Patch any existing build directories
echo -e "\n=== Patching existing pyjnius build directories ==="
find .buildozer/android/platform/build-*/other_builds/pyjnius* -name "jnius_utils.pxi" -type f 2>/dev/null | while read -r file; do
    echo "Patching build file: $file"
    
    # Add compatibility alias
    if ! grep -q "long = int" "$file"; then
        sed -i '1i try:\n    long\nexcept NameError:\n    long = int\n' "$file"
    fi
    
    # Replace occurrences
    sed -i 's/isinstance(arg, long)/isinstance(arg, int)/g' "$file"
done

# Step 4: Create a build hook to automatically patch new extractions
echo -e "\n=== Creating automated patch hook ==="
cat > patch_pyjnius_hook.sh << 'HOOK_EOF'
#!/bin/bash
# Auto-patch script that runs before pyjnius compilation

echo "Running pyjnius auto-patch hook..."

# Find and patch any jnius_utils.pxi files
find . -name "jnius_utils.pxi" -type f 2>/dev/null | while read -r file; do
    if grep -q "isinstance(arg, long)" "$file" 2>/dev/null; then
        echo "Auto-patching: $file"
        # Add alias
        if ! grep -q "long = int" "$file"; then
            sed -i '1i try:\n    long\nexcept NameError:\n    long = int\n' "$file"
        fi
        # Replace occurrences
        sed -i 's/isinstance(arg, long)/isinstance(arg, int)/g' "$file"
    fi
done
HOOK_EOF

chmod +x patch_pyjnius_hook.sh

# Step 5: Verification
echo -e "\n=== Verification ==="
remaining=$(find . -name "*.pxi" -exec grep -l "isinstance(arg, long)" {} \; 2>/dev/null)
if [ -z "$remaining" ]; then
    echo "✓ No remaining isinstance(arg, long) found in .pxi files"
else
    echo "⚠ Still found isinstance(arg, long) in:"
    echo "$remaining"
fi

# Step 6: Clean build caches to force rebuild
echo -e "\n=== Cleaning pyjnius build caches ==="
rm -rf .buildozer/android/platform/build-*/other_builds/pyjnius* 2>/dev/null
rm -rf .buildozer/android/platform/build-*/dists/*/libs/arm* 2>/dev/null
echo "Cleaned pyjnius build caches"

echo -e "\n=== Patch complete ==="
echo "Now run: buildozer -v android debug"
echo ""
echo "If the error persists, run this script again DURING the build:"
echo "1. Start build: buildozer -v android debug &"
echo "2. When it fails, run: ./patch_pyjnius_hook.sh"
echo "3. Continue/restart build"
