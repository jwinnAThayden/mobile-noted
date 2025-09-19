<!--
  Copilot Instructions for Noted Project
  Last updated: 2025-09-19
-->

# Copilot Instructions for Noted Project

## Overview

**Noted** is a cross-platform note-taking suite with two main apps:
- **Desktop (noted.py):** Tkinter/ttk app for Windows/Linux with multi-pane/tabbed views, OneDrive sync, and session persistence.
- **Mobile (mobile-noted/):** Kivy-based Android app with touch UI, local/cloud storage, and desktop test harness.

## Architecture & Key Patterns

- **Desktop:**
  - `EditableBoxApp` manages all UI, view state, and file/cloud operations.
  - Supports both paned and tabbed views; switching is seamless and stateful.
  - OneDrive integration uses device flow auth and persistent token cache (`onedrive_token_cache.json`).
  - Layout and config are JSON, stored in OneDrive Documents/Noted if available.
  - Progress bars shown for long-running startup/shutdown/cloud operations.
  - All file ops and UI updates are wrapped in try/except for resilience.

- **Mobile:**
  - `MobileNotedApp` (Kivy) with `NoteCard` widgets and spellcheck.
  - Storage path is platform-aware; can migrate between local and cloud.
  - Desktop logic can be tested via `test_desktop.py` (no Kivy required).

## Developer Workflows

- **Desktop:**
  - Run: `python noted.py`
  - Layout auto-saves; OneDrive sync requires `NOTED_CLIENT_ID` env var.
  - Progress bars appear on load/exit/cloud sync.
  - Debug output is printed for key actions (tab creation, sync, errors).

- **Mobile:**
  - Test logic: `cd mobile-noted && python test_desktop.py`
  - Full Kivy: `python mobile-noted.py`
  - Android build: `./build_android.sh` (Linux/WSL recommended)

## Project Conventions

- **Config:** All settings in JSON; always provide defaults if load fails.
- **File I/O:** Always use try/except; log and fallback on error.
- **OneDrive:**
  - Device flow auth; token cache is loaded/saved on every auth/sync.
  - Auth persists for 30 days; user is prompted only if token is expired.
  - All OneDrive features are gated on `NOTED_CLIENT_ID` and successful auth.
- **UI:**
  - All dialogs and progress bars use ttk/Tkinter for consistent look.
  - Tab/box titles are always content-derived (first line/30 chars).
  - Right-click menus for tabs/boxes provide rename/save/close actions.
- **Testing:**
  - Desktop: manual run, check debug output, verify tab/pane switching, OneDrive sync.
  - Mobile: use `test_desktop.py` for logic, Kivy for UI, Android for full test.

## Integration Points

- **OneDrive:**
  - Desktop and mobile both use device flow and store notes as JSON in `/Apps/Noted/`.
  - Web/Mobile can sync via the same app registration and file format.
- **Web:**
  - See `web-mobile-noted.py` for Flask-based web version with similar config/env patterns.

## Key Files & References

- `noted.py` — Desktop app main logic and UI
- `mobile-noted/mobile-noted.py` — Mobile app main logic
- `mobile-noted/README.md` — Mobile build/test instructions
- `CROSS_PLATFORM_ONEDRIVE_INTEGRATION.md` — OneDrive setup and usage
- `ONEDRIVE_RAILWAY_DEPLOYMENT.md` — Web/Cloud deployment and sync
- `README.md` — Project structure and quickstart

---
**AI agents:**
- Always prefer existing patterns and error handling in `noted.py` and `mobile-noted.py`.
- When adding features, update both desktop and mobile if logic is shared.
- Use debug print/log for new behaviors; keep UI feedback clear and consistent.