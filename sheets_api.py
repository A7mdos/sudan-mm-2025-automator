"""
Google Sheets API integration module.
Handles reading from and writing to Google Sheets.
"""

import json
from typing import Optional, List, Dict
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


class SheetsAPI:
    """Wrapper class for Google Sheets API operations."""
    
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    
    def __init__(self, credentials_path: str):
        """
        Initialize Sheets API client.
        
        Args:
            credentials_path: Path to service account credentials JSON file
        """
        self.credentials_path = credentials_path
        self.service = self._authenticate()
    
    def _authenticate(self):
        """Authenticate and return Sheets service object."""
        try:
            creds = service_account.Credentials.from_service_account_file(
                self.credentials_path,
                scopes=self.SCOPES
            )
            return build('sheets', 'v4', credentials=creds)
        except Exception as e:
            raise Exception(f"Failed to authenticate with Google Sheets: {str(e)}")
    
    def find_spreadsheet_by_name(self, spreadsheet_name: str) -> Optional[str]:
        """
        Find a spreadsheet by name using Drive API.
        
        Args:
            spreadsheet_name: Name of the spreadsheet to find
            
        Returns:
            Spreadsheet ID if found, None otherwise
        """
        # Import here to avoid circular imports
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
        creds = service_account.Credentials.from_service_account_file(
            self.credentials_path,
            scopes=['https://www.googleapis.com/auth/drive']
        )
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
        # Import here to avoid circular imports
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        
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
                creds = service_account.Credentials.from_service_account_file(
                    self.credentials_path,
                    scopes=['https://www.googleapis.com/auth/drive']
                )
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
