"""
OneDrive Manager for Noted
Handles Microsoft Graph API authentication and file operations.
"""

import msal
import requests
import json
import os
import time
from threading import Thread

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
    """
    def __init__(self):
        self._token_cache = msal.SerializableTokenCache()
        if os.path.exists(TOKEN_CACHE_FILE):
            self._token_cache.deserialize(open(TOKEN_CACHE_FILE, "r").read())

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
            with open(TOKEN_CACHE_FILE, "w") as f:
                f.write(self._token_cache.serialize())

    def get_account(self):
        """Get the first available account from the cache."""
        accounts = self.app.get_accounts()
        if accounts:
            return accounts[0]
        return None

    def authenticate(self):
        """
        Authenticate the user. Tries to get a token silently first,
        then falls back to interactive device flow.
        """
        self.account = self.get_account()
        if self.account:
            result = self.app.acquire_token_silent(SCOPES, account=self.account)
            if result and "access_token" in result:
                self.access_token = result["access_token"]
                self._save_cache()
                return True, "Authenticated silently."
        
        # Fallback to device flow
        flow = self.app.initiate_device_flow(scopes=SCOPES)
        if "user_code" not in flow:
            return False, "Failed to initiate device flow."

        # Display message to user and poll for token
        print(f"Please go to {flow['verification_uri']} and enter the code: {flow['user_code']}")
        
        # This part is tricky in a GUI. We'll need to handle this with a thread.
        # For now, this is a blocking call for demonstration.
        result = self.app.acquire_token_by_device_flow(flow)

        if result and "access_token" in result:
            self.access_token = result["access_token"]
            self.account = self.get_account() # Refresh account info
            self._save_cache()
            return True, "Authenticated successfully."
        
        return False, "Authentication failed or was cancelled."

    def is_authenticated(self):
        """Check if we have a valid token."""
        self.account = self.get_account()
        if not self.account:
            return False
        
        result = self.app.acquire_token_silent(SCOPES, account=self.account)
        if result and "access_token" in result:
            self.access_token = result['access_token']
            return True
        return False

    def get_headers(self):
        """Get the required headers for Graph API calls."""
        if not self.access_token:
            raise Exception("Not authenticated. Cannot make API calls.")
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def get_user_info(self):
        """Get the signed-in user's display name and email."""
        if not self.is_authenticated():
            return None
        try:
            response = requests.get("https://graph.microsoft.com/v1.0/me", headers=self.get_headers())
            response.raise_for_status()
            user_data = response.json()
            return {
                "name": user_data.get("displayName"),
                "email": user_data.get("mail") or user_data.get("userPrincipalName")
            }
        except requests.exceptions.RequestException as e:
            print(f"Error getting user info: {e}")
            return None

    def list_notes(self):
        """List all .txt files in the app's root folder on OneDrive."""
        if not self.is_authenticated():
            return []
        try:
            response = requests.get(f"{GRAPH_API_ENDPOINT}/children", headers=self.get_headers())
            response.raise_for_status()
            items = response.json().get("value", [])
            # Assuming notes are stored as .json files with content inside
            return [item for item in items if item["name"].endswith(".json")]
        except requests.exceptions.RequestException as e:
            print(f"Error listing notes: {e}")
            return []

    def get_note_content(self, item_id):
        """Get the content of a specific note by its OneDrive item ID."""
        if not self.is_authenticated():
            return None
        try:
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/content"
            response = requests.get(url, headers=self.get_headers())
            response.raise_for_status()
            return response.json() # Assuming content is JSON
        except requests.exceptions.RequestException as e:
            print(f"Error getting note content for {item_id}: {e}")
            return None

    def save_note(self, file_name, content_dict):
        """
        Save a note to OneDrive. Creates or overwrites the file.
        Content is a dictionary that will be saved as a JSON string.
        """
        if not self.is_authenticated():
            return None
        try:
            # Ensure file_name ends with .json
            if not file_name.endswith(".json"):
                file_name += ".json"
            
            url = f"{GRAPH_API_ENDPOINT}:/{file_name}:/content"
            headers = self.get_headers()
            headers["Content-Type"] = "application/json" # We are sending JSON data
            
            response = requests.put(url, headers=headers, data=json.dumps(content_dict))
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error saving note {file_name}: {e}")
            return None

    def delete_note(self, item_id):
        """Delete a note from OneDrive by its item ID."""
        if not self.is_authenticated():
            return False
        try:
            url = f"https://graph.microsoft.com/v1.0/me/drive/items/{item_id}"
            response = requests.delete(url, headers=self.get_headers())
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            print(f"Error deleting note {item_id}: {e}")
            return False

# Example usage (for testing)
if __name__ == "__main__":
    if not CLIENT_ID:
        print("FATAL: NOTED_CLIENT_ID environment variable is not set.")
        print("Please create an Azure App Registration and set this variable.")
    else:
        manager = OneDriveManager()
        is_auth, message = manager.authenticate()
        print(message)

        if is_auth:
            user = manager.get_user_info()
            if user:
                print(f"Signed in as: {user['name']} ({user['email']})")

            print("\nListing notes...")
            notes = manager.list_notes()
            if not notes:
                print("No notes found. Creating a test note.")
                test_note_content = {"content": "This is a test note from OneDriveManager.", "last_modified": time.time()}
                manager.save_note("test_note.json", test_note_content)
                notes = manager.list_notes()

            for note in notes:
                print(f"- {note['name']} (ID: {note['id']})")
                content = manager.get_note_content(note['id'])
                print(f"  Content: {content.get('content', 'N/A')[:50]}...")

            # Example of deleting a note (be careful!)
            # if notes:
            #     print(f"\nDeleting {notes[0]['name']}...")
            #     success = manager.delete_note(notes[0]['id'])
            #     print(f"Deletion successful: {success}")
