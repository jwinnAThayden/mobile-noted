<!--
  Copilot Instructions for Noted Project
  Last updated: 2025-01-19
-->

# Copilot Instructions for Noted Project

## Overview

**Noted** is a cross-platform note-taking suite with three deployment targets:
- **Desktop (noted.py):** Tkinter/ttk app for Windows/Linux with tabbed interface, OneDrive sync, and session persistence.
- **Mobile (mobile-noted/):** Kivy-based Android app with touch UI, local/cloud storage, and desktop test harness.
- **Web (web-mobile-noted.py):** Flask-based web version with similar UI/features, Railway deployment ready.

## Architecture & Key Patterns

- **Desktop (noted.py - 4517 lines):**
  - `EditableBoxApp` manages all UI, view state, file/cloud operations, and session persistence.
  - **TABBED-ONLY INTERFACE:** Paned view completely removed in recent refactor. All UI is now tab-based with `ttk.Notebook`.
  - OneDrive integration via device flow auth and persistent token cache (`onedrive_token_cache.json`).
  - Configuration stored locally by default, with explicit OneDrive sync via UI buttons.
  - Progress bars shown for long-running startup/shutdown/cloud operations.
  - All file operations and UI updates wrapped in try/except for maximum resilience.

- **Mobile (mobile-noted/):**
  - `MobileNotedApp` (Kivy) with `NoteCard` widgets, spell checking, and cross-platform storage.
  - Platform-aware storage paths; seamless migration between local and cloud storage.
  - Desktop logic testable via `test_desktop.py` (no Kivy dependency required).
  - Multiple build variants: `mobile-noted.py` (full), `simple-mobile-noted.py` (minimal).

- **Web (web-mobile-noted.py):**
  - Flask-based with device authentication, CSRF protection, and rate limiting.
  - OneDrive integration via `WebOneDriveManager` with session-based device flows.
  - Railway deployment optimized with health checks and environment variable validation.

## Developer Workflows

- **Desktop:**
  - Run: `python noted.py`
  - Layout auto-saves to local storage; OneDrive sync requires `NOTED_CLIENT_ID` env var.
  - Progress bars appear on load/exit/cloud sync operations.
  - Debug output printed for key actions (tab creation, sync, errors).
  - **Key Change:** Only tabbed interface available; no paned view switching.

- **Mobile:**
  - Test logic: `cd mobile-noted && python test_desktop.py`
  - Full Kivy app: `python mobile-noted.py`
  - Minimal version: `python simple-mobile-noted.py`
  - Android build: `./build_android.sh` (Linux/WSL recommended)
  - Multiple Dockerfile variants for different build approaches.

- **Web:**
  - Development: `python web-mobile-noted.py`
  - Production: Uses `wsgi.py` with comprehensive error handling
  - Railway deployment: Environment variables required for auth

## Project Conventions

- **Config Management:** All settings stored in JSON with mandatory defaults on load failure.
- **Error Resilience:** Every file I/O and UI operation wrapped in try/except with fallback behavior.
- **OneDrive Integration:**
  - Device flow authentication with Microsoft Graph API (`Files.ReadWrite.AppFolder`, `User.Read`).
  - Token cache (`onedrive_token_cache.json`) loaded/saved on every auth/sync operation.
  - Authentication persists for 30 days; user prompted only when token expires.
  - All OneDrive features gated on `NOTED_CLIENT_ID` environment variable and successful auth.
  - Uses Azure App Registration (user must create their own).
- **Storage Strategy:**
  - Desktop: Local storage by default, explicit OneDrive sync via UI.
  - Mobile: Platform-aware paths with fallback storage mechanisms.
  - Web: Session-based with persistent storage and Railway deployment optimization.
- **UI Standards:**
  - Desktop: ttk/Tkinter for all dialogs and progress indicators.
  - Tab titles always content-derived (first line truncated to ~30 chars).
  - Right-click context menus for tabs/notes (rename, save, close actions).
  - Progress feedback for all long-running operations.
- **Testing Approach:**
  - Desktop: Manual testing with debug output verification, tabbed interface focus.
  - Mobile: `test_desktop.py` for core logic, full Kivy for UI, Android for integration.
  - Web: Health check endpoints, environment variable validation, authentication flows.

## Integration Points

- **OneDrive Synchronization:**
  - All platforms use device flow authentication with Microsoft Graph API.
  - Notes stored as JSON in OneDrive `/Apps/Noted/` application folder.
  - Cross-platform compatibility with identical file formats and auth mechanisms.
  - Desktop/Mobile/Web share same Azure App Registration and token cache patterns.
- **Cross-Platform File Format:**
  - JSON-based note storage with consistent schema across all platforms.
  - Configuration files use identical structure and field names.
  - OneDrive manager classes (`OneDriveManager`, `WebOneDriveManager`) share common interface patterns.
- **Build & Deployment:**
  - Mobile: Multiple Docker build strategies, GitHub Actions automation.
  - Web: Railway deployment with health checks and environment validation.
  - Desktop: Direct Python execution with automatic dependency handling.

## Key Files & References

- **Core Applications:**
  - `noted.py` — Desktop app main logic and UI (4517 lines, tabbed-only interface)
  - `mobile-noted/mobile-noted.py` — Full mobile app logic with OneDrive integration
  - `mobile-noted/simple-mobile-noted.py` — Minimal mobile app for reliable builds
  - `web-mobile-noted.py` — Flask web application with OneDrive sync
- **OneDrive Integration:**
  - `onedrive_manager.py` — Desktop OneDrive authentication and sync
  - `mobile-noted/onedrive_manager.py` — Mobile-optimized OneDrive manager
  - `onedrive_web_manager.py` — Web-specific OneDrive manager with session handling
- **Configuration & Testing:**
  - `mobile-noted/test_desktop.py` — Mobile logic testing without Kivy
  - `test_fixes_verification.py` — Verification of critical architectural changes
  - `layout.json` — Desktop UI state persistence
- **Documentation:**
  - `mobile-noted/README.md` — Mobile build/test instructions and Android deployment
  - `WEB-README.md` — Web version setup and browser-based usage
  - `CROSS_PLATFORM_ONEDRIVE_INTEGRATION.md` — OneDrive setup and Azure App Registration
  - `ONEDRIVE_RAILWAY_DEPLOYMENT.md` — Web deployment and cloud synchronization
  - `README.md` — Project structure, quickstart, and architecture overview

## Critical Development Guidelines

**AI agents working on this codebase should:**
- **Maintain Error Resilience:** Every file operation, network request, and UI update must be wrapped in try/except with meaningful fallbacks.
- **Preserve Tabbed Interface:** Desktop app is now tabbed-only; do not attempt to restore paned view functionality.
- **Follow OneDrive Patterns:** All OneDrive integration must use device flow authentication and respect the existing token cache mechanisms.
- **Update Cross-Platform:** When adding features, consider impact on desktop, mobile, and web versions; maintain consistent UX patterns.
- **Use Existing Debug Patterns:** Print debug output for new behaviors; maintain clear UI feedback for long-running operations.
- **Test Storage Fallbacks:** Always implement graceful fallback storage mechanisms when primary storage (OneDrive/custom paths) fails.
- **Preserve JSON Schema:** Maintain compatibility of configuration and note file formats across all platforms.