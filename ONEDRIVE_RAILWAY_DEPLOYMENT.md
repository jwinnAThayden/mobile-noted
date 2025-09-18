# OneDrive Integration for Railway Web Noted

## Overview

The Railway web version of Noted now includes full OneDrive integration to synchronize notes across desktop, mobile, and web platforms. This implementation uses Microsoft Graph API with device flow authentication for secure, browser-based OneDrive access.

## Required Environment Variables

For Railway deployment, you need to set the following environment variables:

### Existing Variables
- `NOTED_USERNAME`: Your login username
- `NOTED_PASSWORD_HASH`: Bcrypt hash of your password
- `SECRET_KEY`: Flask session secret key

### New OneDrive Variables
- `NOTED_CLIENT_ID`: Azure App Registration Client ID for OneDrive access

## Azure App Registration Setup

1. **Create Azure App Registration**:
   - Go to [Azure Portal](https://portal.azure.com) → Azure Active Directory → App registrations
   - Click "New registration"
   - Name: "Noted Web OneDrive Integration"
   - Supported account types: "Accounts in any organizational directory and personal Microsoft accounts"
   - Redirect URI: Leave blank (we use device flow)

2. **Configure API Permissions**:
   - Go to API permissions → Add a permission
   - Microsoft Graph → Delegated permissions
   - Add: `Files.ReadWrite.AppFolder`, `User.Read`, `offline_access`
   - Grant admin consent if required

3. **Get Client ID**:
   - Go to Overview tab
   - Copy the "Application (client) ID"
   - Set this as `NOTED_CLIENT_ID` environment variable in Railway

4. **Enable Public Client**:
   - Go to Authentication → Advanced settings
   - Set "Allow public client flows" to Yes

## Features

### Authentication
- **Device Flow**: Secure browser-based authentication without storing credentials
- **Session Management**: Authentication state persists across browser sessions
- **Auto-Reconnect**: Automatically refreshes tokens when needed

### Synchronization
- **Push to Cloud**: Upload local notes to OneDrive app folder
- **Pull from Cloud**: Download and merge OneDrive notes
- **Auto-Sync**: Automatically sync changes when enabled
- **Conflict Resolution**: Merge strategies for handling conflicts

### User Interface
- **Floating Action Button**: Always-visible OneDrive status indicator
- **Comprehensive Panel**: Full-featured sync controls and settings
- **Real-time Status**: Live connection status and account information
- **Cloud Browser**: View and manage OneDrive notes

## OneDrive Storage Structure

Notes are stored in the OneDrive app folder (`/Apps/Noted/`) in JSON format:
- Each note becomes a `.json` file
- Filename format: `web_note_{timestamp}_{note_id}.json`
- Contains text, timestamps, ownership, and metadata

## Deployment Steps

1. **Update Railway Environment Variables**:
   ```
   NOTED_CLIENT_ID=your-azure-client-id
   ```

2. **Deploy Updated Code**:
   - The OneDrive integration is automatically available when `NOTED_CLIENT_ID` is set
   - If the environment variable is missing, the app runs without OneDrive features

3. **First-Time Setup**:
   - Open your web app
   - Click the OneDrive floating button (☁️)
   - Follow the device flow authentication process
   - Your notes will sync across all platforms

## Cross-Platform Synchronization

With OneDrive integration on all platforms:

### Desktop (noted.py)
- Stores notes in OneDrive Documents folder
- Uses MSAL device flow authentication
- Automatic background sync

### Mobile (mobile-noted/)
- Accesses OneDrive via shared authentication
- Manual and automatic sync options
- Handles mobile-specific storage patterns

### Web (Railway)
- Browser-based OneDrive access
- Device flow for secure authentication
- Real-time sync controls and status

All three platforms now share the same persistent storage, achieving your goal of unified content synchronization.

## Security Features

- **No Stored Credentials**: Uses device flow, no passwords in browser
- **Token Encryption**: Secure token storage and refresh
- **App Folder Isolation**: OneDrive access limited to app-specific folder
- **CSRF Protection**: All API endpoints protected against CSRF attacks
- **Rate Limiting**: Authentication and sync operations are rate-limited

## Troubleshooting

### OneDrive Not Available
- Check `NOTED_CLIENT_ID` environment variable
- Verify Azure app registration configuration
- Ensure internet connectivity

### Authentication Failures
- Verify Azure app permissions are granted
- Check if app registration allows public client flows
- Try clearing browser cache and re-authenticating

### Sync Issues
- Check OneDrive connection status
- Verify sufficient OneDrive storage space
- Try manual sync before enabling auto-sync

## API Endpoints

The integration adds these new REST endpoints:

- `GET /api/onedrive/status` - Check connection status
- `POST /api/onedrive/auth/start` - Start device flow authentication
- `GET /api/onedrive/auth/check` - Check authentication progress
- `POST /api/onedrive/auth/cancel` - Cancel authentication
- `POST /api/onedrive/logout` - Disconnect from OneDrive
- `POST /api/onedrive/sync/push` - Upload notes to OneDrive
- `POST /api/onedrive/sync/pull` - Download notes from OneDrive
- `GET /api/onedrive/notes` - List OneDrive notes

All endpoints require web app authentication and include CSRF protection.

---

This completes the OneDrive integration for unified note synchronization across desktop, mobile, and Railway web platforms!