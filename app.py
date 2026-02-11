"""
Sudan-MM-2025 Automator
Streamlit web application for multimodal data collection workflow.
Deployment-ready version with Streamlit secrets support.
"""

import streamlit as st
import os
import json
import tempfile
from pathlib import Path
from typing import Optional, Dict

from drive_api import DriveAPI
from sheets_api import SheetsAPI
from media_validator import MediaValidator


# Page configuration
st.set_page_config(
    page_title="Sudan-MM Data Collection",
    page_icon="📸",
    layout="wide"
)

# Initialize session state
if 'initialized' not in st.session_state:
    st.session_state.initialized = False
if 'drive_api' not in st.session_state:
    st.session_state.drive_api = None
if 'sheets_api' not in st.session_state:
    st.session_state.sheets_api = None
if 'folder_structure' not in st.session_state:
    st.session_state.folder_structure = None
if 'spreadsheet_id' not in st.session_state:
    st.session_state.spreadsheet_id = None


def load_config() -> Dict:
    """Load configuration from config.json or Streamlit secrets."""
    # Try Streamlit secrets first (deployment)
    try:
        if hasattr(st, 'secrets') and 'config' in st.secrets:
            return dict(st.secrets['config'])
    except:
        pass
    
    # Fall back to config.json (local development)
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("config.json not found and no secrets configured.")
        st.stop()
    except json.JSONDecodeError:
        st.error("Invalid JSON in config.json.")
        st.stop()


def initialize_apis(config: Dict):
    """Initialize Google Drive and Sheets API clients with OAuth."""
    
    # Check if we're running on Streamlit Cloud (secrets available)
    # Only the [token] section is required for deployment.
    # The [oauth_credentials] section is only needed for local re-authentication.
    use_secrets = False
    try:
        if hasattr(st, 'secrets') and 'token' in st.secrets:
            use_secrets = True
    except Exception:
        use_secrets = False
    
    if use_secrets:
        # Deployment mode - use token from secrets
        try:
            # Deep-convert to plain Python dict (handles Streamlit's AttrDict)
            token_dict = json.loads(json.dumps(dict(st.secrets['token']), default=str))
            
            # Initialize APIs with token only (no oauth_credentials needed on server)
            drive_api = DriveAPI(token_dict=token_dict)
            sheets_api = SheetsAPI(token_dict=token_dict)
            
        except Exception as e:
            st.error(f"Failed to initialize with secrets: {str(e)}")
            st.info(
                "**Token may have expired!**\n\n"
                "To fix this:\n"
                "1. Run `python refresh_token.py` locally\n"
                "2. Copy the new token content\n"
                "3. Update the `token` secret in Streamlit Cloud settings\n"
                "4. Restart the app"
            )
            st.stop()
    else:
        # Local mode - use files
        oauth_credentials_path = config.get('oauth_credentials_file', 'oauth_credentials.json')
        
        if not os.path.exists(oauth_credentials_path):
            st.error(f"OAuth credentials file not found: {oauth_credentials_path}")
            st.info(
                "Please download OAuth credentials from Google Cloud Console:\n\n"
                "1. Go to APIs & Services → Credentials\n"
                "2. Create OAuth 2.0 Client ID (Desktop app)\n"
                "3. Download and save as 'oauth_credentials.json'"
            )
            st.stop()
        
        try:
            # Initialize APIs with OAuth files
            drive_api = DriveAPI(oauth_credentials_path)
            sheets_api = SheetsAPI(oauth_credentials_path)
            
        except Exception as e:
            st.error(f"Failed to initialize APIs: {str(e)}")
            st.info(
                "If this is your first time running the app, a browser window should open "
                "for you to authorize the app. If you see a 'Google hasn't verified this app' "
                "warning, click Advanced → Go to [App Name] (unsafe)."
            )
            st.stop()
    
    try:
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
        
        # Get or create spreadsheet
        spreadsheet_name = config.get('spreadsheet_name', 'Sudan-MM-Metadata')
        spreadsheet_id = sheets_api.get_or_create_spreadsheet(
            spreadsheet_name,
            folder_structure.get('parent')
        )
        
        # Store in session state
        st.session_state.drive_api = drive_api
        st.session_state.sheets_api = sheets_api
        st.session_state.folder_structure = folder_structure
        st.session_state.spreadsheet_id = spreadsheet_id
        st.session_state.initialized = True
        
    except Exception as e:
        st.error(f"Failed to set up folders/spreadsheet: {str(e)}")
        st.stop()


def get_next_id(mode: str) -> str:
    """Generate the next sequential ID for the given mode."""
    sheets_api = st.session_state.sheets_api
    spreadsheet_id = st.session_state.spreadsheet_id
    
    max_id = sheets_api.get_max_id(spreadsheet_id, mode)
    next_id_num = max_id + 1
    
    prefix = 'img_' if mode == 'Image' else 'vid_'
    return f"{prefix}{next_id_num}"


def save_uploaded_file(uploaded_file, suffix: str = "") -> Optional[str]:
    """Save uploaded file to temporary location."""
    try:
        suffix = suffix or Path(uploaded_file.name).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getbuffer())
            return tmp_file.name
    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        return None


def safe_delete_file(file_path: str, max_retries: int = 3) -> bool:
    """
    Safely delete a file, handling cases where it might still be in use.
    
    Args:
        file_path: Path to the file to delete
        max_retries: Maximum number of retry attempts
        
    Returns:
        True if deleted successfully, False otherwise
    """
    if not file_path or not os.path.exists(file_path):
        return True
    
    import time
    import gc
    
    for attempt in range(max_retries):
        try:
            # Force garbage collection to close any open file handles
            gc.collect()
            time.sleep(0.1)  # Small delay to allow file handles to close
            os.unlink(file_path)
            return True
        except PermissionError:
            if attempt < max_retries - 1:
                time.sleep(0.5)  # Wait longer before retry
                continue
            # Last attempt failed, log but don't crash
            print(f"Warning: Could not delete temporary file {file_path} after {max_retries} attempts")
            return False
        except Exception as e:
            print(f"Warning: Error deleting file {file_path}: {str(e)}")
            return False
    
    return False


def main():
    """Main application function."""
    st.title("📸 Sudan-MM Data Collection Dashboard")
    st.markdown("Upload multimodal pairs (Media + Text + Voice) for the Sudan-MM-2025 project.")
    
    # Load configuration
    config = load_config()
    
    # Initialize APIs if not already done
    if not st.session_state.initialized:
        with st.spinner("Initializing Google Drive and Sheets APIs..."):
            initialize_apis(config)
        st.success("✅ APIs initialized successfully!")
        st.info("Files will be uploaded to Google Drive and logged in the spreadsheet.")
    
    # Mode selection
    st.divider()
    mode = st.radio(
        "Select Mode",
        ["Image", "Video"],
        horizontal=True,
        help="Choose whether you're submitting an image or video"
    )
    
    # Create form
    with st.form("submission_form", clear_on_submit=True):
        st.subheader(f"📤 Upload {mode}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Media file upload
            if mode == "Image":
                media_file = st.file_uploader(
                    "Upload Image",
                    type=['jpg', 'jpeg', 'png'],
                    help="Supported formats: .jpg, .jpeg, .png"
                )
            else:
                media_file = st.file_uploader(
                    "Upload Video",
                    type=['mp4'],
                    help="Supported format: .mp4 (3-10 seconds)"
                )
        
        with col2:
            # Audio file upload
            audio_file = st.file_uploader(
                "Upload Audio Caption",
                type=['mp3'],
                help="Voice caption in .mp3 format (5-15 seconds)"
            )
        
        # Text captions
        st.subheader("✍️ Captions")
        
        msa_caption = st.text_area(
            "Modern Standard Arabic (MSA) Caption",
            placeholder="Enter caption in Modern Standard Arabic...",
            height=100
        )
        
        sudanese_caption = st.text_area(
            "Sudanese Arabic Caption",
            placeholder="Enter caption in Sudanese Arabic...",
            height=100
        )
        
        # Category dropdown
        categories = [
            "Urban daily life",
            "Rural daily life",
            "Marketplaces",
            "Food",
            "Clothing & textiles",
            "Landscapes & nature",
            "Transportation",
            "Public spaces & infrastructure",
            "Agriculture & livestock",
            "Local objects & cultural items"
        ]
        category = st.selectbox(
            "Category",
            categories,
            help="Select the appropriate category for this submission"
        )
        
        # Submit button
        submitted = st.form_submit_button("Submit", use_container_width=True)
        
        if submitted:
            # Validation
            errors = []
            
            # Check required fields
            if not media_file:
                errors.append("Please upload a media file")
            if not audio_file:
                errors.append("Please upload an audio file")
            if not msa_caption.strip():
                errors.append("MSA caption is required")
            if not sudanese_caption.strip():
                errors.append("Sudanese Arabic caption is required")
            if not category:
                errors.append("Please select a category")
            
            if errors:
                for error in errors:
                    st.error(error)
            else:
                # Process submission
                with st.spinner("Processing submission..."):
                    try:
                        # Save uploaded files temporarily
                        media_ext = Path(media_file.name).suffix
                        media_temp_path = save_uploaded_file(media_file, media_ext)
                        audio_temp_path = save_uploaded_file(audio_file, '.mp3')
                        
                        if not media_temp_path or not audio_temp_path:
                            st.error("Failed to save uploaded files")
                            return
                        
                        # Validate media file format
                        validator = MediaValidator()
                        is_valid, error_msg = validator.validate_media_file(
                            media_temp_path,
                            mode.lower()
                        )
                        if not is_valid:
                            st.error(f"Media validation error: {error_msg}")
                            safe_delete_file(media_temp_path)
                            safe_delete_file(audio_temp_path)
                            return
                        
                        # Validate audio file format
                        is_valid, error_msg = validator.validate_audio_file(audio_temp_path)
                        if not is_valid:
                            st.error(f"Audio validation error: {error_msg}")
                            safe_delete_file(media_temp_path)
                            safe_delete_file(audio_temp_path)
                            return
                        
                        # Validate video duration (close file handles after validation)
                        video_clip = None
                        if mode == "Video":
                            is_valid, error_msg, duration = validator.validate_video_duration(
                                media_temp_path,
                                min_seconds=3.0,
                                max_seconds=10.0
                            )
                            if not is_valid:
                                st.error(f"Video validation error: {error_msg}")
                                safe_delete_file(media_temp_path)
                                safe_delete_file(audio_temp_path)
                                return
                        
                        # Validate audio duration
                        is_valid, error_msg, duration = validator.validate_audio_duration(
                            audio_temp_path,
                            min_seconds=5.0,
                            max_seconds=15.0
                        )
                        if not is_valid:
                            st.error(f"Audio validation error: {error_msg}")
                            safe_delete_file(media_temp_path)
                            safe_delete_file(audio_temp_path)
                            return
                        
                        # Generate next ID
                        next_id = get_next_id(mode)
                        
                        # Rename files with ID
                        media_new_name = f"{next_id}{media_ext}"
                        audio_new_name = f"{next_id}.mp3"
                        
                        # Determine target folders
                        if mode == "Image":
                            media_folder_id = st.session_state.folder_structure['Images']
                            audio_folder_id = st.session_state.folder_structure['Image_Audio_Transcriptions']
                            media_folder_path = "Images"
                            audio_folder_path = "Image_Audio_Transcriptions"
                        else:
                            media_folder_id = st.session_state.folder_structure['Videos']
                            audio_folder_id = st.session_state.folder_structure['Video_Audio_Transcriptions']
                            media_folder_path = "Videos"
                            audio_folder_path = "Video_Audio_Transcriptions"
                        
                        # Upload files to Google Drive
                        drive_api = st.session_state.drive_api
                        
                        media_file_info = drive_api.upload_file(
                            media_temp_path,
                            media_new_name,
                            media_folder_id
                        )
                        
                        audio_file_info = drive_api.upload_file(
                            audio_temp_path,
                            audio_new_name,
                            audio_folder_id
                        )
                        
                        # Prepare metadata row
                        file_link = f"{media_folder_path}/{media_new_name}"
                        audio_file_link = f"{audio_folder_path}/{audio_new_name}"
                        
                        row_data = [
                            next_id,
                            file_link,
                            msa_caption.strip(),
                            sudanese_caption.strip(),
                            audio_file_link,
                            category
                        ]
                        
                        # Append to spreadsheet
                        sheets_api = st.session_state.sheets_api
                        spreadsheet_id = st.session_state.spreadsheet_id
                        sheet_name = 'Images' if mode == 'Image' else 'Videos'
                        
                        sheets_api.append_row(spreadsheet_id, sheet_name, row_data)
                        
                        # Clean up temporary files
                        safe_delete_file(media_temp_path)
                        safe_delete_file(audio_temp_path)
                        
                        # Success message
                        st.success(f"✅ Successfully uploaded {next_id}!")
                        st.balloons()
                        
                        # Display summary
                        with st.expander("View Submission Details", expanded=True):
                            st.write(f"**ID:** {next_id}")
                            st.write(f"**Mode:** {mode}")
                            st.write(f"**Media File:** {media_new_name}")
                            st.write(f"**Audio File:** {audio_new_name}")
                            st.write(f"**Category:** {category}")
                            st.write(f"**MSA Caption:** {msa_caption.strip()}")
                            st.write(f"**Sudanese Caption:** {sudanese_caption.strip()}")
                        
                    except Exception as e:
                        st.error(f"Error processing submission: {str(e)}")
                        # Clean up temp files if they exist
                        if 'media_temp_path' in locals():
                            safe_delete_file(media_temp_path)
                        if 'audio_temp_path' in locals():
                            safe_delete_file(audio_temp_path)


if __name__ == "__main__":
    main()
