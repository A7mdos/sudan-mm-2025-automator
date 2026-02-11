"""
Google Sheets API integration module using OAuth.
Handles reading from and writing to Google Sheets.
Works with both local token files and Streamlit secrets.
"""

import os
import json
import pickle
from typing import Optional, List, Dict
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class SheetsAPI:
    """Wrapper class for Google Sheets API operations using OAuth."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/drive.file',
        'https://www.googleapis.com/auth/spreadsheets'
    ]
    
    def __init__(self, credentials_path: str = None, token_path: str = 'token.pickle',
                 credentials_dict: Dict = None, token_dict: Dict = None):
        """
        Initialize Sheets API client with OAuth.
        
        Args:
            credentials_path: Path to OAuth credentials JSON file (for local)
            token_path: Path to store the token file (for local)
            credentials_dict: OAuth credentials as dict (for Streamlit Cloud)
            token_dict: Token data as dict (for Streamlit Cloud)
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.credentials_dict = credentials_dict
        self.token_dict = token_dict
        self.service = self._authenticate()
    
    def _authenticate(self):
        """Authenticate using OAuth and return Sheets service object."""
        creds = None
        
        # Try loading from Streamlit secrets first (deployment)
        if self.token_dict:
            try:
                # Token provided as dict from Streamlit secrets
                from google.oauth2.credentials import Credentials
                creds = Credentials.from_authorized_user_info(self.token_dict, self.SCOPES)
            except Exception as e:
                raise Exception(f"Failed to load credentials from secrets: {str(e)}")
        # Try loading from file (local development)
        elif os.path.exists(self.token_path):
            try:
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)
            except Exception as e:
                raise Exception(f"Failed to load token from file: {str(e)}")
        
        # If no valid credentials, try to refresh
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    # Save refreshed token
                    if self.token_path and not self.token_dict:
                        with open(self.token_path, 'wb') as token:
                            pickle.dump(creds, token)
                except Exception as e:
                    # If refresh fails in deployment, raise clear error with details
                    if self.token_dict:
                        raise Exception(
                            f"Token expired and could not be refreshed. "
                            f"Google error: {str(e)}. "
                            f"Please run the token refresh script locally and update Streamlit secrets."
                        )
                    # If refresh fails locally, we can't re-authenticate from here
                    raise Exception(f"Authentication failed: {str(e)}")
            else:
                # No valid credentials available
                if self.token_dict:
                    raise Exception(
                        "No valid token found. Please run the app locally to authenticate, "
                        "then update the token in Streamlit secrets."
                    )
                raise Exception("Not authenticated. Please initialize DriveAPI first.")
        
        return build('sheets', 'v4', credentials=creds)
    
    def find_spreadsheet_by_name(self, spreadsheet_name: str) -> Optional[str]:
        """
        Find a spreadsheet by name using Drive API.
        
        Args:
            spreadsheet_name: Name of the spreadsheet to find
            
        Returns:
            Spreadsheet ID if found, None otherwise
        """
        # Get credentials from the token
        creds = None
        if self.token_dict:
            from google.oauth2.credentials import Credentials
            creds = Credentials.from_authorized_user_info(self.token_dict, self.SCOPES)
        elif os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
        
        if not creds:
            raise Exception("Not authenticated. Please initialize DriveAPI first.")
        
        drive_service = build('drive', 'v3', credentials=creds)
        query = f"name='{spreadsheet_name}' and mimeType='application/vnd.google-apps.spreadsheet' and trashed=false"
        
        try:
            results = drive_service.files().list(
                q=query,
                fields="files(id, name)"
            ).execute()
            
            files = results.get('files', [])
            if files:
                return files[0]['id']
            return None
        except HttpError as e:
            raise Exception(f"Error searching for spreadsheet: {str(e)}")
    
    def create_spreadsheet(self, spreadsheet_name: str, parent_folder_id: Optional[str] = None) -> str:
        """
        Create a new spreadsheet with the required tabs and headers.
        
        Args:
            spreadsheet_name: Name of the spreadsheet
            parent_folder_id: Optional parent folder ID to place spreadsheet in
            
        Returns:
            Spreadsheet ID
        """
        # Create spreadsheet
        spreadsheet_body = {
            'properties': {
                'title': spreadsheet_name
            },
            'sheets': [
                {
                    'properties': {
                        'title': 'Images',
                        'gridProperties': {
                            'rowCount': 1000,
                            'columnCount': 6
                        }
                    }
                },
                {
                    'properties': {
                        'title': 'Videos',
                        'gridProperties': {
                            'rowCount': 1000,
                            'columnCount': 6
                        }
                    }
                }
            ]
        }
        
        try:
            spreadsheet = self.service.spreadsheets().create(
                body=spreadsheet_body,
                fields='spreadsheetId'
            ).execute()
            spreadsheet_id = spreadsheet.get('spreadsheetId')
            
            # Set headers for both sheets
            headers = ['id', 'file_link', 'msa_caption', 'sudanese_caption', 'audio_file_link', 'category']
            self.append_row(spreadsheet_id, 'Images', headers)
            self.append_row(spreadsheet_id, 'Videos', headers)
            
            # Move to parent folder if specified
            if parent_folder_id:
                creds = None
                if self.token_dict:
                    from google.oauth2.credentials import Credentials
                    creds = Credentials.from_authorized_user_info(self.token_dict, self.SCOPES)
                elif os.path.exists(self.token_path):
                    with open(self.token_path, 'rb') as token:
                        creds = pickle.load(token)
                
                if not creds:
                    raise Exception("Not authenticated. Please initialize DriveAPI first.")
                
                drive_service = build('drive', 'v3', credentials=creds)
                
                file = drive_service.files().get(
                    fileId=spreadsheet_id,
                    fields='parents'
                ).execute()
                
                previous_parents = ",".join(file.get('parents', []))
                drive_service.files().update(
                    fileId=spreadsheet_id,
                    addParents=parent_folder_id,
                    removeParents=previous_parents,
                    fields='id, parents'
                ).execute()
            
            return spreadsheet_id
        except HttpError as e:
            raise Exception(f"Error creating spreadsheet: {str(e)}")
    
    def get_or_create_spreadsheet(self, spreadsheet_name: str, parent_folder_id: Optional[str] = None) -> str:
        """
        Get existing spreadsheet or create if it doesn't exist.
        
        Args:
            spreadsheet_name: Name of the spreadsheet
            parent_folder_id: Optional parent folder ID
            
        Returns:
            Spreadsheet ID
        """
        spreadsheet_id = self.find_spreadsheet_by_name(spreadsheet_name)
        if spreadsheet_id:
            return spreadsheet_id
        return self.create_spreadsheet(spreadsheet_name, parent_folder_id)
    
    def read_sheet(self, spreadsheet_id: str, sheet_name: str, range_name: Optional[str] = None) -> List[List]:
        """
        Read data from a sheet.
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            sheet_name: Name of the sheet tab
            range_name: Optional range (e.g., 'A1:Z100'), defaults to entire sheet
            
        Returns:
            List of rows (each row is a list of values)
        """
        if range_name:
            range_str = f"{sheet_name}!{range_name}"
        else:
            range_str = sheet_name
        
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id,
                range=range_str
            ).execute()
            return result.get('values', [])
        except HttpError as e:
            raise Exception(f"Error reading sheet: {str(e)}")
    
    def append_row(self, spreadsheet_id: str, sheet_name: str, row_data: List) -> Dict:
        """
        Append a row to a sheet.
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            sheet_name: Name of the sheet tab
            row_data: List of values for the row
            
        Returns:
            Update response
        """
        range_name = f"{sheet_name}!A:A"
        
        value_input_option = 'USER_ENTERED'
        body = {
            'values': [row_data]
        }
        
        try:
            result = self.service.spreadsheets().values().append(
                spreadsheetId=spreadsheet_id,
                range=range_name,
                valueInputOption=value_input_option,
                body=body
            ).execute()
            return result
        except HttpError as e:
            raise Exception(f"Error appending row: {str(e)}")
    
    def get_max_id(self, spreadsheet_id: str, mode: str) -> int:
        """
        Get the maximum ID number for a given mode (img or vid).
        
        Args:
            spreadsheet_id: ID of the spreadsheet
            mode: Either 'Image' or 'Video'
            
        Returns:
            Maximum ID number found (0 if no IDs exist)
        """
        sheet_name = 'Images' if mode == 'Image' else 'Videos'
        rows = self.read_sheet(spreadsheet_id, sheet_name)
        
        if len(rows) <= 1:  # Only headers or empty
            return 0
        
        max_id = 0
        prefix = 'img_' if mode == 'Image' else 'vid_'
        
        # Skip header row (index 0)
        for row in rows[1:]:
            if row and len(row) > 0:
                id_str = str(row[0]).strip()
                if id_str.startswith(prefix):
                    try:
                        # Extract number from id_str (e.g., "img_123" -> 123)
                        num = int(id_str.split('_')[1])
                        max_id = max(max_id, num)
                    except (ValueError, IndexError):
                        continue
        
        return max_id
