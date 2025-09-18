"""
OneDrive Manager for Web Mobile Noted (Railway)
Handles Microsoft Graph API authentication and file operations for Flask web application.
Adapted from desktop/mobile versions with web-specific optimizations.
"""

import msal
import requests
import json
import os
import time
import logging
from threading import Thread, Lock
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# --- Configuration ---
CLIENT_ID = os.environ.get("NOTED_CLIENT_ID") 
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["Files.ReadWrite.AppFolder", "User.Read", "offline_access"]

# API Endpoint for the app's special folder in the user's OneDrive
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0/me/drive/special/approot"

# Use web-specific token cache location
TOKEN_CACHE_FILE = os.path.join(os.path.dirname(__file__), "web_notes", "onedrive_token_cache.json")

class WebOneDriveManager:
    """
    OneDrive Manager optimized for Flask web applications.
    Handles authentication state management and API calls.
    """
    
    def __init__(self):
        # Validate required configuration
        if not CLIENT_ID:
            raise ValueError("NOTED_CLIENT_ID environment variable is required for OneDrive integration")
        
        self._token_cache = msal.SerializableTokenCache()
        self._cache_lock = Lock()
        
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(TOKEN_CACHE_FILE), exist_ok=True)
        
        # Load existing token cache
        if os.path.exists(TOKEN_CACHE_FILE):
            try:
                with open(TOKEN_CACHE_FILE, "r") as f:
                    self._token_cache.deserialize(f.read())
            except Exception as e:
                logger.warning(f"OneDrive: Failed to load token cache: {e}")

        self.app = msal.PublicClientApplication(
            CLIENT_ID,
            authority=AUTHORITY,
            token_cache=self._token_cache
        )
        self.account = None
        self.access_token = None
        self._auth_flows = {}  # Store active auth flows by session ID

    def _save_cache(self):
        """Save the token cache to a file with thread safety."""
        if self._token_cache.has_state_changed:
            try:
                with self._cache_lock:
                    with open(TOKEN_CACHE_FILE, "w") as f:
                        f.write(self._token_cache.serialize())
            except Exception as e:
                logger.error(f"OneDrive: Failed to save token cache: {e}")

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

        try:
            # Try to get token silently first
            result = self.app.acquire_token_silent(SCOPES, account=self.account)
            
            if result and "access_token" in result:
                self.access_token = result["access_token"]
                self._save_cache()
                return self.access_token
        except Exception as e:
            logger.error(f"OneDrive: Token refresh failed: {e}")
            
        return None

    def start_device_flow_auth(self, session_id):
        """
        Start device flow authentication for web sessions.
        Returns flow data for frontend display.
        """
        try:
            flow = self.app.initiate_device_flow(scopes=SCOPES)
            
            if "user_code" not in flow:
                raise ValueError("Failed to create device flow")
            
            # Store flow for this session
            self._auth_flows[session_id] = {
                "flow": flow,
                "started_at": time.time(),
                "completed": False
            }
            
            return {
                "user_code": flow["user_code"],
                "verification_uri": flow["verification_uri"],
                "expires_in": flow.get("expires_in", 900),  # 15 minutes default
                "interval": flow.get("interval", 5)  # 5 seconds default
            }
        except Exception as e:
            logger.error(f"OneDrive: Device flow initiation failed: {e}")
            return None

    def check_device_flow_status(self, session_id):
        """
        Check the status of device flow authentication.
        Returns authentication status and result.
        """
        if session_id not in self._auth_flows:
            return {"status": "not_found", "message": "No authentication flow found"}
        
        flow_data = self._auth_flows[session_id]
        
        if flow_data["completed"]:
            return flow_data["result"]
        
        try:
            # Check if flow has expired
            if time.time() - flow_data["started_at"] > flow_data["flow"].get("expires_in", 900):
                del self._auth_flows[session_id]
                return {"status": "expired", "message": "Authentication flow expired"}
            
            # Try to complete the device flow
            result = self.app.acquire_token_by_device_flow(flow_data["flow"])
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                self.account = self.get_account()
                self._save_cache()
                
                # Mark as completed
                flow_data["completed"] = True
                flow_data["result"] = {"status": "success", "message": "Authentication successful"}
                
                logger.info("OneDrive: Web authentication successful")
                return flow_data["result"]
            
            elif "error" in result:
                if result["error"] == "authorization_pending":
                    return {"status": "pending", "message": "Waiting for user authorization"}
                elif result["error"] == "slow_down":
                    return {"status": "pending", "message": "Slow down polling"}
                else:
                    error_msg = result.get("error_description", result["error"])
                    flow_data["completed"] = True
                    flow_data["result"] = {"status": "error", "message": f"Authentication failed: {error_msg}"}
                    return flow_data["result"]
            
            return {"status": "pending", "message": "Authentication in progress"}
            
        except Exception as e:
            logger.error(f"OneDrive: Device flow status check failed: {e}")
            flow_data["completed"] = True
            flow_data["result"] = {"status": "error", "message": f"Authentication error: {str(e)}"}
            return flow_data["result"]

    def cancel_device_flow(self, session_id):
        """Cancel an active device flow."""
        if session_id in self._auth_flows:
            del self._auth_flows[session_id]
            return True
        return False

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
                
            # Clear any active flows
            self._auth_flows.clear()
                
            logger.info("OneDrive: Web logout successful")
            return True
            
        except Exception as e:
            logger.error(f"OneDrive: Logout error: {e}")
            return False

    def _make_graph_request(self, method, endpoint, data=None, headers=None):
        """Make authenticated request to Microsoft Graph API."""
        token = self._get_access_token()
        if not token:
            raise Exception("Not authenticated with OneDrive")

        request_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        if headers:
            request_headers.update(headers)

        url = f"https://graph.microsoft.com/v1.0{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=request_headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                if isinstance(data, str):
                    # For content uploads
                    request_headers["Content-Type"] = "application/json"
                    response = requests.put(url, headers=request_headers, data=data, timeout=30)
                else:
                    response = requests.put(url, headers=request_headers, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=request_headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            if response.status_code not in [200, 201, 204]:
                logger.error(f"OneDrive: API request failed: {response.status_code} - {response.text}")
                response.raise_for_status()

            return response

        except requests.exceptions.RequestException as e:
            logger.error(f"OneDrive: Request failed: {e}")
            raise Exception(f"OneDrive API request failed: {str(e)}")

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
                        "size": file["size"],
                        "download_url": file.get("@microsoft.graph.downloadUrl")
                    })
                    
            return sorted(notes, key=lambda x: x["modified"], reverse=True)
            
        except Exception as e:
            logger.error(f"OneDrive: Failed to list notes: {e}")
            return []

    def get_note(self, note_id):
        """Download a note by its OneDrive ID."""
        try:
            response = self._make_graph_request("GET", f"/me/drive/items/{note_id}/content")
            return json.loads(response.text)
            
        except Exception as e:
            logger.error(f"OneDrive: Failed to get note {note_id}: {e}")
            return None

    def save_note(self, note_data, note_id=None):
        """
        Save a note to OneDrive.
        If note_id is provided, update existing note.
        Otherwise, create new note.
        """
        try:
            content = json.dumps(note_data, indent=2)
            
            if note_id:
                # Update existing note
                response = self._make_graph_request(
                    "PUT", 
                    f"/me/drive/items/{note_id}/content",
                    data=content
                )
            else:
                # Create new note with timestamp-based filename
                filename = f"web_note_{int(time.time())}.json"
                
                response = self._make_graph_request(
                    "PUT",
                    f"/me/drive/special/approot:/{filename}:/content",
                    data=content
                )
                
            result = response.json()
            logger.info(f"OneDrive: Note saved successfully: {result.get('name', 'unknown')}")
            return result.get("id")
            
        except Exception as e:
            logger.error(f"OneDrive: Failed to save note: {e}")
            return None

    def delete_note(self, note_id):
        """Delete a note from OneDrive."""
        try:
            self._make_graph_request("DELETE", f"/me/drive/items/{note_id}")
            logger.info(f"OneDrive: Note {note_id} deleted successfully")
            return True
            
        except Exception as e:
            logger.error(f"OneDrive: Failed to delete note {note_id}: {e}")
            return False

    def sync_notes_to_cloud(self, local_notes):
        """
        Sync local notes to OneDrive.
        Returns dict with sync results and updated notes with OneDrive IDs.
        """
        if not self.is_authenticated():
            return {
                "success": False,
                "error": "Not authenticated with OneDrive",
                "notes": local_notes
            }

        try:
            # Get existing OneDrive notes
            onedrive_notes = self.list_notes()
            onedrive_map = {note["name"]: note for note in onedrive_notes}
            
            synced_notes = {}
            sync_stats = {"created": 0, "updated": 0, "errors": 0}
            
            for note_id, note_data in local_notes.items():
                try:
                    # Generate consistent filename
                    timestamp = note_data.get("created", "unknown")
                    safe_timestamp = timestamp.replace(":", "-").replace(".", "-")
                    filename = f"note_{safe_timestamp}_{note_id}.json"
                    
                    # Prepare note data for OneDrive
                    cloud_note_data = {
                        **note_data,
                        "web_note_id": note_id,
                        "synced_at": datetime.now().isoformat()
                    }
                    
                    if filename in onedrive_map:
                        # Update existing note
                        onedrive_id = onedrive_map[filename]["id"]
                        saved_id = self.save_note(cloud_note_data, onedrive_id)
                        if saved_id:
                            note_data["onedrive_id"] = saved_id
                            sync_stats["updated"] += 1
                        else:
                            sync_stats["errors"] += 1
                    else:
                        # Create new note
                        saved_id = self.save_note(cloud_note_data)
                        if saved_id:
                            note_data["onedrive_id"] = saved_id
                            sync_stats["created"] += 1
                        else:
                            sync_stats["errors"] += 1
                    
                    synced_notes[note_id] = note_data
                    
                except Exception as e:
                    logger.error(f"OneDrive: Failed to sync note {note_id}: {e}")
                    synced_notes[note_id] = note_data
                    sync_stats["errors"] += 1
            
            logger.info(f"OneDrive: Web sync completed - {sync_stats}")
            return {
                "success": True,
                "stats": sync_stats,
                "notes": synced_notes
            }
            
        except Exception as e:
            logger.error(f"OneDrive: Sync operation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "notes": local_notes
            }

    def load_notes_from_cloud(self):
        """
        Load all notes from OneDrive.
        Returns dict with notes formatted for web application.
        """
        if not self.is_authenticated():
            return {
                "success": False,
                "error": "Not authenticated with OneDrive",
                "notes": {}
            }

        try:
            onedrive_notes = self.list_notes()
            loaded_notes = {}
            load_stats = {"loaded": 0, "errors": 0}
            
            for note_info in onedrive_notes:
                try:
                    note_data = self.get_note(note_info["id"])
                    if note_data:
                        # Use web_note_id if available, otherwise generate one
                        note_id = note_data.get("web_note_id", str(int(time.time() * 1000)))
                        
                        # Clean up OneDrive-specific fields for web use
                        web_note_data = {
                            "text": note_data.get("text", ""),
                            "created": note_data.get("created", note_info["modified"]),
                            "modified": note_data.get("modified", note_info["modified"]),
                            "owner": note_data.get("owner", "onedrive"),
                            "onedrive_id": note_info["id"]
                        }
                        
                        loaded_notes[note_id] = web_note_data
                        load_stats["loaded"] += 1
                        
                except Exception as e:
                    logger.error(f"OneDrive: Failed to load note {note_info['id']}: {e}")
                    load_stats["errors"] += 1
            
            logger.info(f"OneDrive: Loaded {load_stats['loaded']} notes from cloud")
            return {
                "success": True,
                "stats": load_stats,
                "notes": loaded_notes
            }
            
        except Exception as e:
            logger.error(f"OneDrive: Failed to load notes from cloud: {e}")
            return {
                "success": False,
                "error": str(e),
                "notes": {}
            }

    def get_auth_status(self):
        """Get current authentication status for frontend."""
        return {
            "authenticated": self.is_authenticated(),
            "account_info": {
                "username": self.account.get("username") if self.account else None,
                "home_account_id": self.account.get("home_account_id") if self.account else None
            } if self.account else None
        }