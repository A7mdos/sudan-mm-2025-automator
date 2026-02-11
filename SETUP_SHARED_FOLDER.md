# How to Set Up Shared Folder for Service Account

## Why This is Required

Service accounts have very limited storage (15GB total across all service accounts in a project). To avoid quota errors, you MUST share a folder from YOUR Google Drive with the service account.

## Step-by-Step Instructions

### 1. Get Your Service Account Email

Your service account email is: **sudan-mm-2025-app@sudan-mm-2025-automator.iam.gserviceaccount.com**

(You can also find this in `service_account_credentials.json` as the `client_email` field)

### 2. Create or Choose a Folder in YOUR Google Drive

1. Go to [Google Drive](https://drive.google.com)
2. Create a new folder OR choose an existing one where you want files to be stored
3. **IMPORTANT**: This folder must be in YOUR personal Google Drive, NOT in the service account's drive

### 3. Share the Folder with the Service Account

1. Right-click the folder → **Share**
2. In the "Add people and groups" field, paste: `sudan-mm-2025-app@sudan-mm-2025-automator.iam.gserviceaccount.com`
3. Set permissions to **Editor**
4. **CRITICAL**: **UNCHECK** "Notify people" (service accounts can't receive email notifications)
5. Click **Share** or **Send**

### 4. Get the Folder ID

1. Open the folder in Google Drive
2. Look at the URL in your browser: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
3. Copy the `FOLDER_ID_HERE` part (it's a long string of letters, numbers, and dashes)

### 5. Update config.json

Open `config.json` and set `shared_folder_id` to the folder ID you copied:

```json
{
  "team_name": "Zamanna",
  "spreadsheet_name": "Sudan-MM-Submission-Zamanna",
  "parent_folder_name": "Sudan-MM-Submission-Zamanna",
  "shared_folder_id": "YOUR_FOLDER_ID_HERE",
  "service_account_file": "service_account_credentials.json"
}
```

### 6. Verify the Setup

1. Restart the Streamlit app
2. Check the sidebar - it should show "✅ Shared folder configured"
3. Try uploading a file - it should work without quota errors

## Troubleshooting

### Still Getting Storage Quota Errors?

1. **Verify the folder is shared correctly**:
   - Go to the folder in Google Drive
   - Click the "Share" button
   - Check that `sudan-mm-2025-app@sudan-mm-2025-automator.iam.gserviceaccount.com` appears in the list
   - Make sure it has "Editor" permissions

2. **Check the folder ID**:
   - Make sure you copied the entire folder ID from the URL
   - The folder ID should be in `config.json` as a string (with quotes)

3. **Make sure the folder is in YOUR drive**:
   - The folder should appear in your Google Drive
   - If you created it in the service account's drive, it won't work - create a new folder in YOUR drive

4. **Try sharing again**:
   - Remove the service account from the folder
   - Share it again, making sure "Notify people" is UNCHECKED

### Permission Denied Errors?

- Make sure the service account has "Editor" permissions (not just "Viewer")
- Try removing and re-adding the service account to the folder

### Folder Not Found Errors?

- Double-check the folder ID in `config.json`
- Make sure the folder still exists in Google Drive
- Verify the folder ID matches what's in the URL when you open the folder
