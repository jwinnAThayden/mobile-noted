[app]

# (str) Title of your application
title = Simple Mobile Noted

# (str) Package name
package.name = simplemobilenoted

# (str) Package domain (needed for android/ios packaging)
package.domain = com.haydenbeverage.simplemobilenoted

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,json,txt

# (list) List of directory/patterns to exclude from package
source.exclude_dirs = tests, test, testing, __pycache__, *.pyc, *.pyo, .git, .svn, .hg, .bzr
source.exclude_patterns = */test_*, */tests/*, test_*.py, *_test.py

# (str) Application versioning (method 1)
version = 1.0

# (list) Application requirements
# Note: android and pyjnius are automatically included by buildozer for Android builds
# Using minimal stable versions to avoid compilation issues
requirements = python3,kivy

# (str) Presplash of the application
#presplash.filename = %(source.dir)s/data/presplash.png

# (str) Icon of the application
#icon.filename = %(source.dir)s/data/icon.png

# (str) Supported orientation (landscape, portrait or all)
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET

# (int) Android API to use
android.api = 31

# (int) Minimum API required
android.minapi = 21

# (str) Android NDK version to use
android.ndk = 25b

# (str) python-for-android git url (if not set, defaults to upstream)
p4a.source_dir = 

# (str) The directory in which python-for-android should look for your own build recipes (if any)
p4a.local_recipes = 

# (str) Filename to the hook for p4a
p4a.hook = 

# (str) Bootstrap to use for creating the application
p4a.bootstrap = sdl2

# (int) port number to specify an explicit --port= p4a argument (eg for bootstrap flask)
p4a.port =

# (bool) Use --private data storage (True) or --dir public storage (False)
android.private_storage = True

# (list) Android architectures to build for
android.archs = armeabi-v7a,arm64-v8a

# (str) Android SDK path (auto-detected by buildozer if not set)
#android.sdk_path = 

# (str) Android NDK path (auto-detected by buildozer if not set)
#android.ndk_path = 

# (bool) If True, then skip trying to update the Android sdk
# This can be useful to avoid excess Internet downloads or save time
# when an update is due and you just want to test/build your package
android.skip_update = False

# (bool) If True, then automatically accept SDK license
# agreements. This is intended for automation only. If set to False,
# the default, you will be shown the license when first running
# buildozer.
android.accept_sdk_license = True

# (list) Python modules/packages to exclude from the build
android.blacklist = test,tests,lib2to3.tests,unittest,doctest,pdb,pydoc,sqlite3.test,tkinter,turtle

# (str) Python optimization level for bytecode compilation (-O)
python.optimize = 2

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug (with command output))
log_level = 2

# (str) Path to build artifact storage, absolute or relative to spec file
# build_dir = ./.buildozer

# (str) Path to build output (i.e. .apk, .aab, .ipa) storage
# bin_dir = ./bin
