"""
OneDrive Manager for Mobile Noted
Handles Microsoft Graph API authentication and file operations.
Adapted from desktop version for Kivy/mobile use.
"""

import msal
import requests
import json
import os
import time
from threading import Thread
from kivy.logger import Logger
from kivy.utils import platform

# --- Configuration ---
# This Client ID is for the user's own Azure AD App Registration
# The user must create this themselves.
CLIENT_ID = os.environ.get("NOTED_CLIENT_ID") 
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["Files.ReadWrite.AppFolder", "User.Read", "offline_access"]

# API Endpoint for the app's special folder in the user's OneDrive
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0/me/drive/special/approot"

TOKEN_CACHE_FILE = "onedrive_token_cache.json"

class OneDriveManager:
    """
    A class to manage authentication and file sync with OneDrive.
    Mobile-optimized version with Kivy logger integration.
    """
    def __init__(self):
        self._token_cache = msal.SerializableTokenCache()
        if os.path.exists(TOKEN_CACHE_FILE):
            try:
                with open(TOKEN_CACHE_FILE, "r") as f:
                    self._token_cache.deserialize(f.read())
            except Exception as e:
                Logger.warning(f"OneDrive: Failed to load token cache: {e}")

        self.app = msal.PublicClientApplication(
            CLIENT_ID,
            authority=AUTHORITY,
            token_cache=self._token_cache
        )
        self.account = None
        self.access_token = None

    def _save_cache(self):
        """Save the token cache to a file."""
        if self._token_cache.has_state_changed:
            try:
                with open(TOKEN_CACHE_FILE, "w") as f:
                    f.write(self._token_cache.serialize())
            except Exception as e:
                Logger.error(f"OneDrive: Failed to save token cache: {e}")

    def get_account(self):
        """Get the first available account from the cache."""
        accounts = self.app.get_accounts()
        if accounts:
            return accounts[0]
        return None

    def is_authenticated(self):
        """Check if we have a valid account and token."""
        if not self.account:
            self.account = self.get_account()
        
        if self.account and self._get_access_token():
            return True
        return False

    def _get_access_token(self):
        """Get a valid access token, refreshing if necessary."""
        if not self.account:
            self.account = self.get_account()
            if not self.account:
                return None

        # Try to get token silently first
        result = self.app.acquire_token_silent(SCOPES, account=self.account)
        
        if result and "access_token" in result:
            self.access_token = result["access_token"]
            self._save_cache()
            return self.access_token
            
        return None

    def start_device_flow_auth(self):
        """
        Start device flow authentication.
        Returns (user_code, verification_url, device_code) for UI display.
        """
        try:
            flow = self.app.initiate_device_flow(scopes=SCOPES)
            
            if "user_code" not in flow:
                raise ValueError("Failed to create device flow")
                
            return (
                flow["user_code"],
                flow["verification_uri"], 
                flow
            )
        except Exception as e:
            Logger.error(f"OneDrive: Device flow initiation failed: {e}")
            return None, None, None

    def complete_device_flow_auth(self, flow):
        """Complete the device flow authentication in a separate thread."""
        def auth_worker():
            try:
                result = self.app.acquire_token_by_device_flow(flow)
                
                if "access_token" in result:
                    self.access_token = result["access_token"]
                    self.account = self.get_account()
                    self._save_cache()
                    Logger.info("OneDrive: Authentication successful")
                    return True
                else:
                    error = result.get("error_description", "Unknown error")
                    Logger.error(f"OneDrive: Authentication failed: {error}")
                    return False
            except Exception as e:
                Logger.error(f"OneDrive: Authentication error: {e}")
                return False
        
        # Start authentication in background thread
        thread = Thread(target=auth_worker, daemon=True)
        thread.start()
        return thread

    def logout(self):
        """Clear authentication and remove cached tokens."""
        try:
            if self.account:
                self.app.remove_account(self.account)
            
            self.account = None
            self.access_token = None
            
            # Clear token cache file
            if os.path.exists(TOKEN_CACHE_FILE):
                os.remove(TOKEN_CACHE_FILE)
                
            Logger.info("OneDrive: Logged out successfully")
            return True
            
        except Exception as e:
            Logger.error(f"OneDrive: Logout error: {e}")
            return False

    def _make_graph_request(self, method, endpoint, data=None, headers=None):
        """Make authenticated request to Microsoft Graph API."""
        token = self._get_access_token()
        if not token:
            raise Exception("Not authenticated")

        request_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        if headers:
            request_headers.update(headers)

        url = f"https://graph.microsoft.com/v1.0{endpoint}"
        
        if method.upper() == "GET":
            response = requests.get(url, headers=request_headers)
        elif method.upper() == "POST":
            response = requests.post(url, headers=request_headers, json=data)
        elif method.upper() == "PUT":
            response = requests.put(url, headers=request_headers, json=data)
        elif method.upper() == "DELETE":
            response = requests.delete(url, headers=request_headers)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")

        if response.status_code not in [200, 201, 204]:
            Logger.error(f"OneDrive: API request failed: {response.status_code} - {response.text}")
            response.raise_for_status()

        return response

    def list_notes(self):
        """List all note files in OneDrive app folder."""
        try:
            response = self._make_graph_request("GET", "/me/drive/special/approot/children")
            files = response.json().get("value", [])
            
            # Filter for .json files (our note format)
            notes = []
            for file in files:
                if file["name"].endswith(".json"):
                    notes.append({
                        "id": file["id"],
                        "name": file["name"],
                        "modified": file["lastModifiedDateTime"],
                        "size": file["size"]
                    })
                    
            return sorted(notes, key=lambda x: x["modified"], reverse=True)
            
        except Exception as e:
            Logger.error(f"OneDrive: Failed to list notes: {e}")
            return []

    def get_note(self, note_id):
        """Download a note by its OneDrive ID."""
        try:
            response = self._make_graph_request("GET", f"/me/drive/items/{note_id}/content")
            return json.loads(response.text)
            
        except Exception as e:
            Logger.error(f"OneDrive: Failed to get note {note_id}: {e}")
            return None

    def save_note(self, note_data, note_id=None):
        """
        Save a note to OneDrive.
        If note_id is provided, update existing note.
        Otherwise, create new note.
        """
        try:
            if note_id:
                # Update existing note
                content = json.dumps(note_data, indent=2)
                headers = {"Content-Type": "application/json"}
                
                response = self._make_graph_request(
                    "PUT", 
                    f"/me/drive/items/{note_id}/content",
                    data=content,
                    headers=headers
                )
            else:
                # Create new note
                filename = f"note_{int(time.time())}.json"
                content = json.dumps(note_data, indent=2)
                
                # Upload new file
                headers = {"Content-Type": "application/json"}
                response = self._make_graph_request(
                    "PUT",
                    f"/me/drive/special/approot:/{filename}:/content",
                    data=content,
                    headers=headers
                )
                
            result = response.json()
            Logger.info(f"OneDrive: Note saved successfully: {result.get('name', 'unknown')}")
            return result.get("id")
            
        except Exception as e:
            Logger.error(f"OneDrive: Failed to save note: {e}")
            return None

    def delete_note(self, note_id):
        """Delete a note from OneDrive."""
        try:
            self._make_graph_request("DELETE", f"/me/drive/items/{note_id}")
            Logger.info(f"OneDrive: Note {note_id} deleted successfully")
            return True
            
        except Exception as e:
            Logger.error(f"OneDrive: Failed to delete note {note_id}: {e}")
            return False

    def sync_local_notes(self, local_notes_data):
        """
        Sync local notes with OneDrive.
        Returns updated notes data with OneDrive IDs.
        """
        if not self.is_authenticated():
            Logger.warning("OneDrive: Not authenticated, skipping sync")
            return local_notes_data

        try:
            # Get existing OneDrive notes
            onedrive_notes = self.list_notes()
            
            # Create mapping of existing notes by filename
            onedrive_map = {note["name"]: note for note in onedrive_notes}
            
            synced_notes = {}
            
            for note_id, note_data in local_notes_data.items():
                # Generate consistent filename from note data
                title = note_data.get("title", "untitled")
                filename = f"{title.replace(' ', '_')}_{note_id}.json"
                
                if filename in onedrive_map:
                    # Update existing note
                    onedrive_id = onedrive_map[filename]["id"]
                    saved_id = self.save_note(note_data, onedrive_id)
                    if saved_id:
                        note_data["onedrive_id"] = saved_id
                else:
                    # Create new note
                    saved_id = self.save_note(note_data)
                    if saved_id:
                        note_data["onedrive_id"] = saved_id
                
                synced_notes[note_id] = note_data
            
            Logger.info(f"OneDrive: Synced {len(synced_notes)} notes")
            return synced_notes
            
        except Exception as e:
            Logger.error(f"OneDrive: Sync failed: {e}")
            return local_notes_data