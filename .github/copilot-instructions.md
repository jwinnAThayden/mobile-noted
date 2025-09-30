<!--
  Copilot Instructions for Noted Project
  Last updated: 2025-09-30
-->

# Copilot Instructions for Noted Project

## Overview

**Noted** is a cross-platform note-taking suite with three deployment targets:
- **Desktop (noted.py):** Tkinter/ttk app with tabbed interface, OneDrive sync, and session persistence stored in `layout.json`.
- **Mobile (mobile-noted/):** Kivy-based Android app with touch UI, GitHub Actions APK builds, and desktop test harness.
- **Web (web-mobile-noted.py - 2053 lines):** Flask-based web version with Railway deployment, authentication-optional design, comprehensive OneDrive integration, and complex JavaScript UI.

## Architecture & Key Patterns

- **Desktop (noted.py):**
  - `EditableBoxApp` class manages all UI state, file operations, and cloud sync.
  - **Tabbed-only interface** with `ttk.Notebook` - no paned views.
  - OneDrive integration via device flow auth with persistent `onedrive_token_cache.json`.
  - Session state persisted in `layout.json` with "onedrive:" prefixed file paths for cloud files.
  - All operations wrapped in try/except with graceful fallbacks and user feedback.

- **Mobile (mobile-noted/):**
  - `MobileNotedApp` (Kivy) with touch-optimized `NoteCard` widgets.
  - **Desktop testing harness** via `test_desktop.py` (tkinter-based, no Kivy dependency).
  - Android APK builds via GitHub Actions with multiple build strategies (`build_android.sh`).
  - Platform-aware storage with OneDrive integration and local fallbacks.

- **Web (web-mobile-noted.py - 2053 lines):**
  - Flask app with **authentication-optional design** - works with or without `NOTED_USERNAME`/`NOTED_PASSWORD_HASH`.
  - `WebOneDriveManager` for session-based device flow authentication.
  - Railway deployment via `Procfile` with gunicorn and 120s timeouts.
  - CSRF protection conditionally enabled only when authentication is active.
  - Extensive timeout handling (45s auth checks, 60s status calls, 90s retries) optimized for Railway's environment.
  - **Critical JavaScript patterns**: Single-page app (6648-line `templates/index.html`) with complex template literal handling, OneDrive browsing UI, bulk operations with checkboxes, and device flow authentication modals.

## Developer Workflows

- **Desktop Testing:**
  ```bash
  python noted.py  # Full desktop app with OneDrive sync
  ```
  - Layout persists across sessions in `layout.json`
  - OneDrive requires `NOTED_CLIENT_ID` environment variable
  - Debug output shows tab operations and sync status

- **Mobile Development:**
  ```bash
  cd mobile-noted
  python test_desktop.py     # Test mobile logic without Kivy
  python mobile-noted.py     # Full Kivy app for desktop testing
  ./build_android.sh         # Build APK (Linux/WSL recommended)
  ```

- **Web Development:**
  ```bash
  python web-mobile-noted.py  # Development server
  # Railway deployment via git push (automatic via Procfile)
  ```
  - **JavaScript debugging**: Use string concatenation instead of nested template literals to avoid parsing errors
  - **OneDrive testing**: Use `/debug/onedrive` endpoint for integration status without authentication

- **Testing Pattern:** Create `test_*.py` files for verification - examples: `test_network_error_fix.py`, `test_onedrive_dialog_fix.py`, `test_auth_fix.py`

## Project Conventions

- **Error Resilience:** All file I/O, network calls, and UI operations use try/except with meaningful fallbacks and user notifications.
- **OneDrive Integration:**
  - Microsoft Graph API with device flow authentication (`Files.ReadWrite.AppFolder`, `User.Read`).
  - Files stored with "onedrive:" prefixes in `layout.json`: `"file_path": "onedrive:01G3ZRC7BCQHWWYOYY3JHKKP66ADJX4MRY"`.
  - Token caching patterns shared across all platforms but adapted per environment.
  - Authentication state managed per session for web, persistent for desktop/mobile.
- **Configuration Management:**
  - JSON-based settings with mandatory defaults on load failure.
  - Platform-specific paths: Railway uses `/app/flask_session/`, desktop uses local directories.
- **UI Patterns:**
  - Desktop: Tab titles derived from first line of content, truncated to ~30 chars.
  - Web: Modal dialogs with device flow progress displays, comprehensive CSRF handling.
  - Mobile: Touch-friendly card interfaces with swipe scrolling.
- **JavaScript Patterns (Web):**
  - **Avoid nested template literals**: Use string concatenation with `+` operator to prevent parsing errors.
  - **Unicode handling**: Replace Unicode emojis with plain text in JavaScript strings (e.g., `✅` → `✓`).
  - **Function scope**: Attach event handlers to `window` object for global access in template-generated code.
  - **Bulk operations**: Selection state managed through checkboxes with `updateSelectedCount()` and `toggleSelectAllNotes()` functions.

## Critical Integration Points

- **OneDrive File References:** Files prefixed with "onedrive:" in configs contain Microsoft Graph file IDs, not local paths.
- **Cross-Platform Auth:** All platforms use same `CLIENT_ID` but different token storage strategies (files vs sessions vs memory).
- **Railway Deployment:** 
  - Authentication optional (determined by environment variables)
  - CSRF protection dynamically enabled/disabled based on auth status
  - Extended timeouts for Microsoft device flow compatibility
- **Mobile APK Builds:** GitHub Actions automated builds with artifact downloads, multiple Dockerfile strategies for build resilience.

## Key Files & Debugging

- **Core Applications:** `noted.py` (desktop), `mobile-noted/mobile-noted.py`, `web-mobile-noted.py` (Flask)
- **OneDrive Managers:** `onedrive_manager.py`, `onedrive_web_manager.py` - different auth patterns per platform
- **Testing:** `mobile-noted/test_desktop.py` (mobile logic), `test_*.py` files for specific feature verification
- **Configuration:** `layout.json` (desktop state), `Procfile` (Railway deployment), `buildozer.spec` (Android builds)
- **Templates:** `templates/index.html` (web UI with device flow dialogs and CSRF handling)

## Critical Development Guidelines

**AI agents working on this codebase should:**
- **Maintain Authentication Flexibility:** Web version must work with or without authentication - check `AUTH_ENABLED` flag patterns.
- **Preserve OneDrive File ID Format:** Never modify "onedrive:" prefixed paths - these are Microsoft Graph file identifiers.
- **Follow Timeout Patterns:** Use extended timeouts (45s-90s) for Railway deployment compatibility.
- **Test Cross-Platform:** When modifying OneDrive integration, verify desktop, mobile, and web versions maintain compatibility.
- **Use Existing Error Patterns:** Wrap all operations in try/except with user-visible feedback and graceful degradation.
- **Respect Platform Differences:** Desktop uses persistent files, web uses sessions, mobile uses platform storage - don't cross-pollinate patterns.
- **Maintain Test Harnesses:** Use `test_desktop.py` for mobile logic testing, create `test_*.py` for feature verification.
- **JavaScript Best Practices:** 
  - Convert nested template literals to string concatenation to avoid parsing errors
  - Remove Unicode characters from JavaScript strings that could break parsing
  - Attach functions to `window` object when they need global scope
  - Use `/debug/onedrive` for testing without authentication requirements