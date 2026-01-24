"""
Google Drive API integration module using OAuth.
Handles authentication, folder creation, and file uploads.
"""

import os
import json
import pickle
from typing import Optional, Dict
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


class DriveAPI:
    """Wrapper class for Google Drive API operations using OAuth."""
    
    SCOPES = ['https://www.googleapis.com/auth/drive.file']
    
    def __init__(self, credentials_path: str, token_path: str = 'token.pickle'):
        """
        Initialize Drive API client with OAuth.
        
        Args:
            credentials_path: Path to OAuth credentials JSON file (from Google Cloud Console)
            token_path: Path to store the token file (persists login across sessions)
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = self._authenticate()
    
    def _authenticate(self):
        """Authenticate using OAuth and return Drive service object."""
        creds = None
        
        # Load token if it exists
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, let user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    # If refresh fails, delete token and re-authenticate
                    os.remove(self.token_path)
                    creds = None
            
            if not creds:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES)
                    creds = flow.run_local_server(port=0)
                except Exception as e:
                    raise Exception(
                        f"Failed to authenticate. Make sure you have created OAuth credentials.\n"
                        f"Error: {str(e)}\n\n"
                        f"Instructions:\n"
                        f"1. Go to Google Cloud Console\n"
                        f"2. APIs & Services → Credentials\n"
                        f"3. Create OAuth 2.0 Client ID (Desktop app)\n"
                        f"4. Download and save as 'oauth_credentials.json'"
                    )
            
            # Save credentials for next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        return build('drive', 'v3', credentials=creds)
    
    def find_folder_by_name(self, folder_name: str, parent_id: Optional[str] = None) -> Optional[str]:
        """
        Find a folder by name, optionally within a parent folder.
        
        Args:
            folder_name: Name of the folder to find
            parent_id: Optional parent folder ID to search within
            
        Returns:
            Folder ID if found, None otherwise
        """
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        try:
            results = self.service.files().list(
                q=query,
                fields="files(id, name)",
                spaces='drive'
            ).execute()
            
            folders = results.get('files', [])
            if folders:
                return folders[0]['id']
            return None
        except HttpError as e:
            raise Exception(f"Error searching for folder: {str(e)}")
    
    def create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """
        Create a folder in Google Drive.
        
        Args:
            folder_name: Name of the folder to create
            parent_id: Optional parent folder ID
            
        Returns:
            Created folder ID
        """
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_id:
            file_metadata['parents'] = [parent_id]
        
        try:
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            return folder.get('id')
        except HttpError as e:
            raise Exception(f"Error creating folder '{folder_name}': {str(e)}")
    
    def get_or_create_folder(self, folder_name: str, parent_id: Optional[str] = None) -> str:
        """
        Get existing folder or create if it doesn't exist.
        
        Args:
            folder_name: Name of the folder
            parent_id: Optional parent folder ID
            
        Returns:
            Folder ID
        """
        folder_id = self.find_folder_by_name(folder_name, parent_id)
        if folder_id:
            return folder_id
        return self.create_folder(folder_name, parent_id)
    
    def upload_file(self, file_path: str, file_name: str, folder_id: str, mime_type: Optional[str] = None) -> Dict:
        """
        Upload a file to Google Drive.
        
        Args:
            file_path: Local path to the file
            file_name: Name to use for the file in Drive
            folder_id: ID of the folder to upload to
            mime_type: Optional MIME type (auto-detected if not provided)
            
        Returns:
            Dictionary with file information including 'id' and 'name'
        """
        file_metadata = {
            'name': file_name,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
        
        try:
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink'
            ).execute()
            return file
        except HttpError as e:
            raise Exception(f"Error uploading file '{file_name}': {str(e)}")
    
    def verify_folder_access(self, folder_id: str) -> bool:
        """
        Verify that we can access a folder.
        
        Args:
            folder_id: ID of the folder to verify
            
        Returns:
            True if accessible, raises exception otherwise
        """
        try:
            folder = self.service.files().get(
                fileId=folder_id,
                fields='id, name, mimeType'
            ).execute()
            
            if folder.get('mimeType') != 'application/vnd.google-apps.folder':
                raise Exception(f"ID {folder_id} is not a folder")
            
            return True
        except HttpError as e:
            error_str = str(e)
            if 'not found' in error_str.lower() or '404' in error_str:
                raise Exception(f"Folder {folder_id} not found. Please check the folder ID.")
            elif 'permission' in error_str.lower() or '403' in error_str:
                raise Exception(f"Permission denied for folder {folder_id}.")
            raise Exception(f"Cannot access folder {folder_id}: {error_str}")
    
    def setup_folder_structure(self, parent_folder_name: str, parent_folder_id: Optional[str] = None) -> Dict[str, str]:
        """
        Set up the required folder structure for the application.
        
        Args:
            parent_folder_name: Name of the parent folder
            parent_folder_id: Optional ID of existing parent folder
            
        Returns:
            Dictionary mapping folder names to their IDs
        """
        # Use existing parent folder or create new one
        if parent_folder_id:
            self.verify_folder_access(parent_folder_id)
            parent_id = parent_folder_id
        else:
            parent_id = self.get_or_create_folder(parent_folder_name)
        
        # Define subfolders
        subfolders = [
            'Images',
            'Videos',
            'Image_Audio_Transcriptions',
            'Video_Audio_Transcriptions'
        ]
        
        folder_ids = {'parent': parent_id}
        
        # Create or get each subfolder
        for subfolder in subfolders:
            folder_id = self.get_or_create_folder(subfolder, parent_id)
            folder_ids[subfolder] = folder_id
        
        return folder_ids
