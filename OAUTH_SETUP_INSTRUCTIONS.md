# OAuth Setup Instructions for Sudan-MM App

Your app is currently using a **service account**, which doesn't work with personal Gmail accounts because service accounts don't have storage quota. You need to switch to **OAuth 2.0** authentication.

## Steps to Switch to OAuth:

### 1. Create OAuth Credentials in Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project: `sudan-mm-2025-automator`
3. Navigate to **APIs & Services** → **Credentials**
4. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
5. If prompted, configure the OAuth consent screen:
   - User Type: **External**
   - App name: `Sudan-MM-2025 App`
   - User support email: Your email
   - Developer contact: Your email
   - Click **Save and Continue**
   - Scopes: Click **Save and Continue** (no need to add scopes manually)
   - Test users: Add your email address (a7mdos1999@gmail.com or whichever you'll use)
   - Click **Save and Continue**
6. Back on the Credentials page, click **+ CREATE CREDENTIALS** → **OAuth client ID**
7. Application type: **Desktop app**
8. Name: `Sudan-MM Desktop Client`
9. Click **Create**
10. Click **DOWNLOAD JSON** and save it as `oauth_credentials.json` in your project folder

### 2. Replace Your Files

Replace these files in your project:

1. **Replace `drive_api.py`** with the new `drive_api_oauth.py` (rename it to `drive_api.py`)
2. **Replace `config.json`** with the new `config_oauth.json` (rename it to `config.json`)
3. **Add the `oauth_credentials.json`** file you downloaded from step 1

### 3. Update Your App Initialization

In your `app.py`, find this section (around line 51-63):

```python
def initialize_apis(config: Dict):
    """Initialize Google Drive and Sheets API clients."""
    credentials_path = config.get('service_account_file', 'service_account_credentials.json')
    
    if not os.path.exists(credentials_path):
        st.error(f"Service account credentials file not found: {credentials_path}")
        st.info("Please place your service_account_credentials.json file in the project root.")
        st.stop()
    
    try:
        # Initialize APIs
        drive_api = DriveAPI(credentials_path)
        sheets_api = SheetsAPI(credentials_path)
```

**Replace it with:**

```python
def initialize_apis(config: Dict):
    """Initialize Google Drive and Sheets API clients."""
    oauth_credentials_path = config.get('oauth_credentials_file', 'oauth_credentials.json')
    
    if not os.path.exists(oauth_credentials_path):
        st.error(f"OAuth credentials file not found: {oauth_credentials_path}")
        st.info("Please download OAuth credentials from Google Cloud Console and save as oauth_credentials.json")
        st.stop()
    
    try:
        # Initialize APIs with OAuth
        drive_api = DriveAPI(oauth_credentials_path)
        sheets_api = SheetsAPI(oauth_credentials_path)
```

And update the folder setup part (around line 65-91):

```python
        # Set up folder structure
        parent_folder_name = config.get('parent_folder_name', 'Sudan-MM-Submission-Zamanna')
        parent_folder_id = config.get('parent_folder_id')
        
        if parent_folder_id and parent_folder_id.strip():
            # Use existing folder
            folder_structure = drive_api.setup_folder_structure(
                parent_folder_name, 
                parent_folder_id=parent_folder_id.strip()
            )
        else:
            # Create new folder structure
            folder_structure = drive_api.setup_folder_structure(parent_folder_name)
```

### 4. Update SheetsAPI to Use OAuth

You'll also need to update your `sheets_api.py` to use OAuth instead of service account. The changes are similar:

- Change the authentication to use OAuth (same as drive_api.py)
- Remove the `supportsAllDrives` parameters

### 5. First Run

When you first run the app:

1. A browser window will open asking you to sign in to Google
2. Sign in with your Gmail account (a7mdos1999@gmail.com or another)
3. You might see a warning "Google hasn't verified this app" - click **Advanced** → **Go to Sudan-MM-2025 App (unsafe)**
4. Click **Allow** to grant permissions
5. The browser will show "The authentication flow has completed"
6. Close the browser and return to your app

A `token.pickle` file will be created to remember your login. You won't need to sign in again unless you delete this file or the token expires.

### 6. Remove Old Files (Optional)

Once everything works, you can delete:
- `service_account_credentials.json`
- The old `shared_folder_id` from your config (not needed anymore)

## Advantages of OAuth:

✅ Files upload to YOUR Google Drive (your storage quota)
✅ Works with personal Gmail accounts
✅ No need for Google Workspace
✅ You can access the files directly from your Google Drive

## Need the Updated SheetsAPI?

Let me know if you need me to update your `sheets_api.py` file as well!
