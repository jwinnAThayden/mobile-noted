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
import hashlib
import logging
from threading import Thread, Lock
from datetime import datetime
from flask import session as flask_session

# Configure logging
logger = logging.getLogger(__name__)

# --- Configuration ---
CLIENT_ID = os.environ.get("NOTED_CLIENT_ID", "cf7bb4c5-7271-4caf-adb3-f8f1f1bef9d5") 
# Use common endpoint to support both personal and work/school Microsoft accounts
AUTHORITY = "https://login.microsoftonline.com/common"
SCOPES = ["Files.ReadWrite.AppFolder", "User.Read"]

# API Endpoint for the app's special folder in the user's OneDrive
GRAPH_API_ENDPOINT = "https://graph.microsoft.com/v1.0/me/drive/special/approot"

# For Railway deployment, store token cache in a persistent location
# Railway containers are ephemeral, but we can use session storage
IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None

if IS_RAILWAY:
    # On Railway, use a more persistent directory structure
    TOKEN_CACHE_FILE = "/app/flask_session/onedrive_token_cache.json"
else:
    # Local development
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
        
        logger.info(f"Initializing WebOneDriveManager with CLIENT_ID: {CLIENT_ID[:8]}...")
        
        try:
            self._token_cache = msal.SerializableTokenCache()
            self._cache_lock = Lock()
            self._use_session_storage = IS_RAILWAY  # Use Flask session storage on Railway
            
            # Ensure cache directory exists
            os.makedirs(os.path.dirname(TOKEN_CACHE_FILE), exist_ok=True)
            
            # Load existing token cache (Railway-aware)
            self._load_token_cache()

            self.app = msal.PublicClientApplication(
                CLIENT_ID,
                authority=AUTHORITY,
                token_cache=self._token_cache
            )
            
            if not self.app:
                raise ValueError("Failed to create MSAL PublicClientApplication")
                
            logger.info("MSAL PublicClientApplication created successfully")
            
            self.account = None
            self.access_token = None
            self._auth_flows = {}  # Store active auth flows by session ID
            
            # Try to restore authentication state from Flask session
            if self._use_session_storage:
                self._restore_from_session()
            
            logger.info("WebOneDriveManager initialization completed successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize WebOneDriveManager: {e}")
            import traceback
            logger.error(f"Initialization traceback: {traceback.format_exc()}")
            raise

    def _load_token_cache(self):
        """Load token cache from persistent storage."""
        try:
            # On Railway, try Flask session first
            if self._use_session_storage and 'onedrive_token_cache' in flask_session:
                token_data = flask_session['onedrive_token_cache']
                if token_data:
                    self._token_cache.deserialize(token_data)
                    logger.info("✅ Token cache loaded from Flask session")
                    return
            
            # Try environment variable (for Railway persistence)
            token_data = os.environ.get('ONEDRIVE_TOKEN_CACHE')
            if token_data:
                self._token_cache.deserialize(token_data)
                logger.info("✅ Token cache loaded from environment variable")
                return
            
            # Fallback to file-based cache
            if os.path.exists(TOKEN_CACHE_FILE):
                with open(TOKEN_CACHE_FILE, "r") as f:
                    self._token_cache.deserialize(f.read())
                    logger.info("✅ Token cache loaded from file")
            else:
                logger.info("ℹ️ No existing token cache found - fresh start")
                
        except Exception as e:
            logger.warning(f"OneDrive: Failed to load token cache: {e}")

    def _save_cache(self):
        """Save token cache with Railway persistence support."""
        if self._token_cache.has_state_changed:
            try:
                with self._cache_lock:
                    token_data = self._token_cache.serialize()
                    
                    # On Railway, save to Flask session for better persistence
                    if self._use_session_storage and token_data:
                        flask_session['onedrive_token_cache'] = token_data
                        flask_session.permanent = True  # Make session persist longer
                        logger.info("✅ Token cache saved to Flask session")
                    
                    # Always try to save to file (for local development)
                    try:
                        os.makedirs(os.path.dirname(TOKEN_CACHE_FILE), exist_ok=True)
                        with open(TOKEN_CACHE_FILE, "w") as f:
                            f.write(token_data)
                        logger.info("✅ Token cache saved to file")
                    except Exception as e:
                        logger.warning(f"File save failed (expected on Railway): {e}")
                    
                    # Log token for Railway environment variable setup as backup
                    if IS_RAILWAY and token_data and len(token_data) > 10:
                        logger.info("🔑 FOR RAILWAY PERSISTENCE (BACKUP):")
                        logger.info("If session storage fails, copy the token below and set it as ONEDRIVE_TOKEN_CACHE environment variable:")
                        logger.info(f"TOKEN: {token_data}")
                    
            except Exception as e:
                logger.error(f"OneDrive: Failed to save token cache: {e}")

    def _restore_from_session(self):
        """Restore authentication state from Flask session."""
        try:
            # Restore account info if available
            if 'onedrive_account' in flask_session:
                account_data = flask_session['onedrive_account']
                # The account will be restored from token cache when needed
                logger.info("📱 OneDrive account data found in session")
            
            # Check if we have valid tokens in session
            if 'onedrive_token_cache' in flask_session:
                logger.info("🔐 OneDrive token cache found in session - authentication should be restored")
                
        except Exception as e:
            logger.warning(f"Failed to restore OneDrive session: {e}")

    def clear_session_auth(self):
        """Clear OneDrive authentication from Flask session."""
        try:
            if self._use_session_storage:
                flask_session.pop('onedrive_token_cache', None)
                flask_session.pop('onedrive_account', None)
                logger.info("🧹 Cleared OneDrive authentication from session")
                
                # Also clear local state
                self.account = None
                self.access_token = None
                
                # Clear token cache
                if hasattr(self._token_cache, 'add'):
                    # Clear the token cache
                    accounts = self.app.get_accounts()
                    for account in accounts:
                        self.app.remove_account(account)
                
                return True
        except Exception as e:
            logger.error(f"Failed to clear session auth: {e}")
        return False

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
            logger.info(f"Starting device flow for session {session_id}")
            logger.info(f"CLIENT_ID available: {bool(CLIENT_ID)}")
            logger.info(f"MSAL app initialized: {self.app is not None}")
            
            if not CLIENT_ID:
                raise ValueError("CLIENT_ID is not set")
            
            if not self.app:
                raise ValueError("MSAL app not initialized")
                
            # Initiate device flow with explicit timeout
            flow = self.app.initiate_device_flow(scopes=SCOPES)
            logger.info(f"🔍 Device flow initiated, response keys: {list(flow.keys())}")
            
            # Log the actual timeout from Microsoft
            actual_timeout = flow.get("expires_in", 900)
            logger.info(f"🕐 Microsoft set device flow timeout: {actual_timeout} seconds ({actual_timeout/60:.1f} minutes)")
            
            # Check for errors in flow response
            if "error" in flow:
                logger.error(f"🔍 Device flow returned error: {flow.get('error')} - {flow.get('error_description', 'No description')}")
                return None
            
            if "user_code" not in flow:
                logger.error(f"🔍 Device flow missing user_code. Full response: {flow}")
                return None
            
            # Override the timeout if it's too short (extend to 45 minutes max)
            extended_timeout = max(actual_timeout, 2700)  # At least 45 minutes
            flow["expires_in"] = extended_timeout
            
            logger.info(f"🕐 Extended device flow timeout to: {extended_timeout} seconds ({extended_timeout/60:.1f} minutes)")
            
            # Store flow for this session
            self._auth_flows[session_id] = {
                "flow": flow,
                "started_at": time.time(),
                "completed": False,
                "original_expires_in": actual_timeout,
                "extended_expires_in": extended_timeout
            }
            
            logger.info(f"Device flow stored successfully for session {session_id}")
            
            return {
                "user_code": flow["user_code"],
                "verification_uri": flow["verification_uri"],
                "expires_in": extended_timeout,  # Return our extended timeout
                "interval": flow.get("interval", 5)  # 5 seconds default
            }
        except Exception as e:
            logger.error(f"OneDrive: Device flow initiation failed: {e}")
            logger.error(f"Exception type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
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
            # Check if flow has expired using our extended timeout
            elapsed_time = time.time() - flow_data["started_at"]
            timeout = flow_data.get("extended_expires_in", flow_data["flow"].get("expires_in", 2700))
            
            logger.info(f"🕐 Device flow check: {elapsed_time:.0f}s elapsed, timeout is {timeout}s ({timeout/60:.1f}min)")
            
            if elapsed_time > timeout:
                logger.warning(f"🕐 Device flow expired after {elapsed_time:.0f}s (timeout: {timeout}s)")
                del self._auth_flows[session_id]
                return {"status": "expired", "message": f"Authentication flow expired after {timeout/60:.1f} minutes"}
            
            # Try to complete the device flow (auth should not be rushed)
            try:
                result = self.app.acquire_token_by_device_flow(flow_data["flow"])
                
            except Exception as e:
                # Handle specific MSAL timeout/network issues gracefully
                if any(keyword in str(e).lower() for keyword in ['timeout', 'connection', 'network']):
                    logger.info(f"OneDrive: Network/timeout issue during auth check: {e}")
                    return {"status": "pending", "message": "Authentication check in progress..."}
                
                # For other MSAL errors that indicate still pending
                if "authorization_pending" in str(e).lower() or "slow_down" in str(e).lower():
                    return {"status": "pending", "message": "Waiting for user to complete authentication..."}
                    
                raise e
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                self.account = self.get_account()
                self._save_cache()
                
                # Save account info to Flask session for persistence
                if self._use_session_storage and self.account:
                    try:
                        flask_session['onedrive_account'] = {
                            'username': self.account.get('username', ''),
                            'home_account_id': self.account.get('home_account_id', ''),
                            'authenticated_at': time.time()
                        }
                        flask_session.permanent = True
                        logger.info("💾 OneDrive account info saved to session")
                    except Exception as e:
                        logger.warning(f"Failed to save account to session: {e}")
                
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
            # Use shorter timeout for Railway deployment to prevent worker timeouts
            request_timeout = 15 if IS_RAILWAY else 30
            
            if method.upper() == "GET":
                response = requests.get(url, headers=request_headers, timeout=request_timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=request_headers, json=data, timeout=request_timeout)
            elif method.upper() == "PUT":
                if isinstance(data, str):
                    # For content uploads
                    request_headers["Content-Type"] = "application/json"
                    response = requests.put(url, headers=request_headers, data=data, timeout=request_timeout)
                else:
                    response = requests.put(url, headers=request_headers, json=data, timeout=request_timeout)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=request_headers, timeout=request_timeout)
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

    def get_note_content(self, item_id):
        """Get the content of a specific note by its OneDrive item ID. Matches desktop interface."""
        return self.get_note(item_id)

    def save_note(self, file_name, content_dict):
        """
        Save a note to OneDrive. Creates or overwrites the file.
        Content is a dictionary that will be saved as a JSON string.
        Compatible with desktop version format.
        """
        try:
            # Ensure file_name ends with .json
            if not file_name.endswith(".json"):
                file_name += ".json"
            
            content = json.dumps(content_dict, indent=2)
            
            response = self._make_graph_request(
                "PUT",
                f"/me/drive/special/approot:/{file_name}:/content",
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
            # Get existing OneDrive notes and build comprehensive mapping
            onedrive_notes = self.list_notes()
            onedrive_map = {note["name"]: note for note in onedrive_notes}
            
            # Build duplicate detection maps
            web_note_id_map = {}  # Map web_note_id to OneDrive filename
            content_hash_map = {}  # Map content hash to OneDrive filename for duplicate detection
            
            # Analyze existing OneDrive notes for duplicates
            for note_info in onedrive_notes:
                try:
                    existing_note_data = self.get_note(note_info["id"])
                    if existing_note_data:
                        # Map by web_note_id for exact matching
                        web_id = existing_note_data.get("web_note_id")
                        if web_id:
                            web_note_id_map[web_id] = note_info["name"]
                        
                        # Map by content hash for duplicate detection
                        content = existing_note_data.get("text", "") or existing_note_data.get("content", "")
                        if content.strip():
                            content_hash = hashlib.md5(content.strip().encode()).hexdigest()
                            if content_hash not in content_hash_map:
                                content_hash_map[content_hash] = []
                            content_hash_map[content_hash].append(note_info["name"])
                except Exception as e:
                    logger.warning(f"Error analyzing existing note {note_info['name']}: {e}")
            
            synced_notes = {}
            sync_stats = {"created": 0, "updated": 0, "errors": 0, "duplicates_avoided": 0}
            
            for note_id, note_data in local_notes.items():
                try:
                    note_text = note_data.get("text", "")
                    content_hash = hashlib.md5(note_text.strip().encode()).hexdigest() if note_text.strip() else None
                    
                    # Check for existing note by web_note_id first (exact match)
                    existing_filename = web_note_id_map.get(note_id)
                    
                    # If not found by web_note_id, check for content duplicates
                    if not existing_filename and content_hash and content_hash in content_hash_map:
                        duplicate_files = content_hash_map[content_hash]
                        if duplicate_files:
                            existing_filename = duplicate_files[0]  # Use first duplicate
                            logger.info(f"Found content duplicate for note {note_id}: {existing_filename}")
                            sync_stats["duplicates_avoided"] += 1
                    
                    # Prepare note data for OneDrive with cross-platform compatibility
                    cloud_note_data = {
                        **note_data,
                        "text": note_text,          # Web format
                        "content": note_text,       # Desktop format
                        "web_note_id": note_id,
                        "synced_at": datetime.now().isoformat(),
                        "source": "web_app"        # Mark as coming from web app
                    }
                    
                    if existing_filename:
                        # Update existing note (either exact match or duplicate)
                        saved_id = self.save_note(existing_filename, cloud_note_data)
                        if saved_id:
                            note_data["onedrive_id"] = saved_id
                            sync_stats["updated"] += 1
                        else:
                            sync_stats["errors"] += 1
                    else:
                        # Create new note with descriptive filename based on title
                        title = note_data.get("title", "").strip()
                        if title and len(title) > 3:
                            # Use title for filename, sanitized
                            safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip()
                            safe_title = safe_title.replace(' ', '_')[:30]  # Limit length
                            new_filename = f"web_{safe_title}_{note_id[:8]}.json"
                        else:
                            # Fallback to timestamp-based filename
                            new_filename = f"web_note_{note_id}_{int(time.time())}.json"
                        
                        saved_id = self.save_note(new_filename, cloud_note_data)
                        if saved_id:
                            note_data["onedrive_id"] = saved_id
                            sync_stats["created"] += 1
                            # Update maps to prevent future duplicates
                            web_note_id_map[note_id] = new_filename
                            if content_hash:
                                if content_hash not in content_hash_map:
                                    content_hash_map[content_hash] = []
                                content_hash_map[content_hash].append(new_filename)
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

    def cleanup_duplicate_notes(self):
        """
        Clean up duplicate notes on OneDrive based on content hash.
        Keeps the most recently modified version of each duplicate.
        """
        if not self.is_authenticated():
            return {
                "success": False,
                "error": "Not authenticated with OneDrive"
            }
        
        try:
            onedrive_notes = self.list_notes()
            content_groups = {}  # Group notes by content hash
            
            # Analyze all notes and group by content
            for note_info in onedrive_notes:
                try:
                    note_data = self.get_note(note_info["id"])
                    if note_data:
                        content = note_data.get("text", "") or note_data.get("content", "")
                        if content.strip():
                            content_hash = hashlib.md5(content.strip().encode()).hexdigest()
                            if content_hash not in content_groups:
                                content_groups[content_hash] = []
                            content_groups[content_hash].append({
                                "filename": note_info["name"],
                                "note_id": note_info["id"],
                                "modified": note_data.get("modified", ""),
                                "created": note_data.get("created", "")
                            })
                except Exception as e:
                    logger.warning(f"Error analyzing note {note_info['name']} for duplicates: {e}")
            
            # Find and remove duplicates
            cleanup_stats = {"duplicates_removed": 0, "groups_processed": 0}
            
            for content_hash, note_group in content_groups.items():
                if len(note_group) > 1:  # Has duplicates
                    cleanup_stats["groups_processed"] += 1
                    # Sort by modified date, keep the most recent
                    note_group.sort(key=lambda x: x["modified"] or x["created"], reverse=True)
                    keeper = note_group[0]
                    duplicates = note_group[1:]
                    
                    logger.info(f"Found {len(duplicates)} duplicates for content hash {content_hash[:8]}...")
                    logger.info(f"Keeping: {keeper['filename']}")
                    
                    # Remove duplicates
                    for duplicate in duplicates:
                        try:
                            if self.delete_note(duplicate["note_id"]):
                                cleanup_stats["duplicates_removed"] += 1
                                logger.info(f"Removed duplicate: {duplicate['filename']}")
                            else:
                                logger.warning(f"Failed to remove duplicate: {duplicate['filename']}")
                        except Exception as e:
                            logger.error(f"Error removing duplicate {duplicate['filename']}: {e}")
            
            logger.info(f"Duplicate cleanup completed: {cleanup_stats}")
            return {
                "success": True,
                "stats": cleanup_stats
            }
            
        except Exception as e:
            logger.error(f"Error during duplicate cleanup: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def load_notes_from_cloud(self, max_notes=50):
        """
        Load notes from OneDrive with Railway deployment optimizations.
        Returns dict with notes formatted for web application.
        Handles both desktop format ('content') and web format ('text') fields.
        """
        if not self.is_authenticated():
            return {
                "success": False,
                "error": "Not authenticated with OneDrive",
                "notes": {}
            }

        try:
            # On Railway, limit the number of notes to prevent timeouts
            if IS_RAILWAY:
                max_notes = min(max_notes, 25)  # Limit to 25 notes on Railway
                logger.info(f"Railway mode: limiting to {max_notes} notes to prevent timeouts")
            
            onedrive_notes = self.list_notes()
            loaded_notes = {}
            load_stats = {"loaded": 0, "errors": 0, "skipped": 0}
            
            # Process notes with a limit to prevent timeout
            notes_to_process = onedrive_notes[:max_notes] if max_notes else onedrive_notes
            
            if len(onedrive_notes) > len(notes_to_process):
                logger.info(f"Processing {len(notes_to_process)} of {len(onedrive_notes)} notes (limited for Railway)")
            
            for i, note_info in enumerate(notes_to_process):
                try:
                    # Early timeout check for Railway deployment
                    if IS_RAILWAY and i > 0 and i % 5 == 0:
                        # Quick break to prevent worker timeout
                        time.sleep(0.1)
                    
                    note_data = self.get_note(note_info["id"])
                    if note_data:
                        # Use web_note_id if available, otherwise generate one
                        note_id = note_data.get("web_note_id", str(int(time.time() * 1000)))
                        
                        # Handle cross-platform content fields
                        # Desktop saves as 'content', web saves as 'text'
                        note_text = ""
                        if "content" in note_data and note_data["content"]:
                            # Desktop format
                            note_text = note_data["content"]
                        elif "text" in note_data and note_data["text"]:
                            # Web format
                            note_text = note_data["text"]
                        
                        # Skip empty notes
                        if not note_text or note_text.strip() == "":
                            logger.info(f"OneDrive: Skipping empty note {note_info['id']}")
                            continue
                        
                        # Clean up OneDrive-specific fields for web use
                        web_note_data = {
                            "text": note_text,
                            "created": note_data.get("created", note_info["modified"]),
                            "modified": note_data.get("modified", note_data.get("last_modified", note_info["modified"])),
                            "owner": note_data.get("owner", note_data.get("source", "onedrive")),
                            "onedrive_id": note_info["id"]
                        }
                        
                        # Handle timestamp format conversion if needed
                        if isinstance(web_note_data["modified"], (int, float)):
                            # Convert Unix timestamp to ISO format
                            web_note_data["modified"] = datetime.fromtimestamp(web_note_data["modified"]).isoformat()
                        
                        loaded_notes[note_id] = web_note_data
                        load_stats["loaded"] += 1
                        logger.info(f"OneDrive: Loaded note {note_id} with content length: {len(note_text)}")
                        
                except Exception as e:
                    logger.error(f"OneDrive: Failed to load note {note_info['id']}: {e}")
                    load_stats["errors"] += 1
                    
                    # On Railway, if we get too many errors, stop to prevent timeout
                    if IS_RAILWAY and load_stats["errors"] > 3:
                        logger.warning("Railway mode: too many errors, stopping note loading to prevent timeout")
                        break
            
            # Add info about skipped notes
            if len(onedrive_notes) > len(notes_to_process):
                load_stats["skipped"] = len(onedrive_notes) - len(notes_to_process)
            
            logger.info(f"OneDrive: Loaded {load_stats['loaded']} notes from cloud (stats: {load_stats})")
            return {
                "success": True,
                "stats": load_stats,
                "notes": loaded_notes,
                "total_available": len(onedrive_notes)
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