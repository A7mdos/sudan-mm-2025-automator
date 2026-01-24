# Sudan-MM-2025 Automator

A Streamlit web application for automating multimodal data collection workflows. This app integrates with Google Drive and Google Sheets APIs to manage file uploads, sequential ID generation, folder organization, and metadata logging.

## Features

- **Dual Mode Support**: Upload images (.jpg, .jpeg, .png) or videos (.mp4)
- **Audio Captions**: Upload .mp3 voice captions for each media file
- **Bilingual Captions**: Support for Modern Standard Arabic (MSA) and Sudanese Arabic captions
- **Category Classification**: 10 predefined categories for organizing submissions
- **Automatic ID Generation**: Sequential IDs (img_1, img_2, vid_1, vid_2, etc.)
- **Smart File Organization**: Automatic routing to appropriate Google Drive folders
- **Metadata Logging**: Automatic logging to Google Sheets with separate tabs for Images and Videos
- **Validation**: Enforces video duration (3-10 seconds) and audio duration (5-15 seconds)

## Prerequisites

1. **Python 3.8+**
2. **Google Cloud Project** with:
   - Google Drive API enabled
   - Google Sheets API enabled
   - Service account credentials JSON file

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** For audio validation, the app uses `mutagen` (recommended, no system dependencies) with `pydub` as a fallback. If you prefer using `pydub` exclusively, you may need to install `ffmpeg` separately on your system.

### 2. Set Up Shared Folder (REQUIRED)

**IMPORTANT**: Service accounts have very limited storage (15GB total across all service accounts). You MUST use a shared folder to avoid quota errors.

1. **Create or choose a folder** in your Google Drive where you want files to be stored
2. **Get your service account email**:
   - Open `service_account_credentials.json`
   - Find the `client_email` field (e.g., `your-service-account@project-id.iam.gserviceaccount.com`)
3. **Share the folder**:
   - Right-click the folder in Google Drive → "Share"
   - Paste the service account email
   - Give it "Editor" permissions
   - Click "Send"
4. **Get the folder ID**:
   - Open the folder in Google Drive
   - Look at the URL: `https://drive.google.com/drive/folders/FOLDER_ID_HERE`
   - Copy the `FOLDER_ID_HERE` part
5. **Add to config.json**: Set `shared_folder_id` to the folder ID you copied

### 3. Configure Google Cloud

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Google Drive API
   - Google Sheets API
4. Create a Service Account:
   - Go to "IAM & Admin" > "Service Accounts"
   - Click "Create Service Account"
   - Give it a name and grant it the following roles:
     - Editor (or custom roles with Drive and Sheets permissions)
   - Create a JSON key and download it
   - Save it as `service_account_credentials.json` in the project root

### 4. Configure Application

Edit `config.json` to set your preferences:

```json
{
  "team_name": "YourTeamName",
  "spreadsheet_name": "Sudan-MM-Metadata",
  "parent_folder_name": "Sudan-MM-Submission-YourTeamName",
  "shared_folder_id": null,
  "service_account_file": "service_account_credentials.json"
}
```

**Important Notes:**
- **Service Account Storage Quota**: Service accounts have very limited storage (15GB total). To avoid quota errors, you MUST share a Google Drive folder with your service account email and set `shared_folder_id` in the config.
- **Setting up Shared Folder**:
  1. Create a folder in your Google Drive (or use an existing one)
  2. Right-click the folder → Share
  3. Add your service account email (found in `service_account_credentials.json` as `client_email`)
  4. Give it "Editor" permissions
  5. Copy the folder ID from the URL (the long string after `/folders/`)
  6. Set `shared_folder_id` in `config.json` to that folder ID
- The `parent_folder_name` will be created inside the shared folder (or in service account's drive if no shared folder is set)
- The spreadsheet will be created automatically if it doesn't exist

## Running the Application

```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`.

## Usage

1. **Select Mode**: Choose between "Image" or "Video" mode
2. **Upload Media**: Upload your image or video file
3. **Upload Audio**: Upload the corresponding .mp3 audio caption
4. **Enter Captions**: Fill in both MSA and Sudanese Arabic captions
5. **Select Category**: Choose the appropriate category from the dropdown
6. **Submit**: Click the submit button to process and upload

The application will:
- Generate the next sequential ID automatically
- Validate file formats and durations
- Rename files with the generated ID
- Upload files to the correct Google Drive folders
- Log metadata to the Google Sheets spreadsheet

## Folder Structure

The application creates the following folder structure in Google Drive:

```
Sudan-MM-Submission-[TeamName]/
├── Images/
├── Videos/
├── Image_Audio_Transcriptions/
└── Video_Audio_Transcriptions/
```

## Spreadsheet Structure

The metadata spreadsheet contains two tabs:

### Images Tab
- `id`: Sequential ID (e.g., img_1, img_2)
- `file_link`: Relative path to image (e.g., Images/img_1.jpg)
- `msa_caption`: Modern Standard Arabic caption
- `sudanese_caption`: Sudanese Arabic caption
- `audio_file_link`: Relative path to audio (e.g., Image_Audio_Transcriptions/img_1.mp3)
- `category`: Selected category

### Videos Tab
- Same structure as Images tab, but with `vid_X` IDs

## Validation Rules

- **Video Duration**: Must be between 3 and 10 seconds
- **Audio Duration**: Must be between 5 and 15 seconds
- **File Formats**: 
  - Images: .jpg, .jpeg, .png
  - Videos: .mp4
  - Audio: .mp3

## Categories

1. Urban daily life
2. Rural daily life
3. Marketplaces
4. Food
5. Clothing & textiles
6. Landscapes & nature
7. Transportation
8. Public spaces & infrastructure
9. Agriculture & livestock
10. Local objects & cultural items

## Troubleshooting

### "Service account credentials file not found"
- Ensure `service_account_credentials.json` is in the project root
- Check that the filename matches the one in `config.json`

### "Failed to authenticate with Google Drive"
- Verify that the service account JSON file is valid
- Ensure the Google Drive API is enabled in your Google Cloud project
- Check that the service account has the necessary permissions

### "Error creating folder" or "Storage quota exceeded"
- **Most common issue**: Service accounts have limited storage. You MUST share a folder with the service account and set `shared_folder_id` in `config.json`
- Verify the service account has permission to create folders in the shared folder
- Check that the shared folder ID is correct in `config.json`
- Ensure the folder is shared with the service account email (found in your credentials JSON file)

## Project Structure

```
.
├── app.py                          # Main Streamlit application
├── drive_api.py                    # Google Drive API integration
├── sheets_api.py                   # Google Sheets API integration
├── media_validator.py              # Media validation utilities
├── config.json                     # Application configuration
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── service_account_credentials.json # Google service account (not in repo)
```

## License

This project is part of the Sudan-MM-2025 data collection initiative.
