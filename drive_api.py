"""
Google Drive API integration module.
Handles authentication, folder creation, and file uploads.
"""

import os
import json
from typing import Optional, Dict
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError


class DriveAPI:
    """Wrapper class for Google Drive API operations."""
    
    SCOPES = ['https://www.googleapis.com/auth/drive']
    
    def __init__(self, credentials_path: str):
        """
        Initialize Drive API client.
        
        Args:
            credentials_path: Path to service account credentials JSON file
        """
        self.credentials_path = credentials_path
        self.service = self._authenticate()
    
    def _authenticate(self):
        """Authenticate and return Drive service object."""
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            return build('drive', 'v3', credentials=creds)
        except Exception as e:
            raise Exception(f"Failed to authenticate with Google Drive: {str(e)}")
    
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
                fields="files(id, name)"
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
            raise Exception(f"Error creating folder: {str(e)}")
    
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
            raise Exception(f"Error uploading file: {str(e)}")
    
    def setup_folder_structure(self, parent_folder_name: str) -> Dict[str, str]:
        """
        Set up the required folder structure for the application.
        
        Args:
            parent_folder_name: Name of the parent folder
            
        Returns:
            Dictionary mapping folder names to their IDs
        """
        # Create or get parent folder
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
