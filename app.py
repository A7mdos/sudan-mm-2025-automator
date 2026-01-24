"""
Sudan-MM-2025 Automator
Streamlit web application for multimodal data collection workflow.
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
    """Load configuration from config.json."""
    try:
        with open('config.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error("config.json not found. Please create it with your settings.")
        st.stop()
    except json.JSONDecodeError:
        st.error("Invalid JSON in config.json.")
        st.stop()


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
        
        # Set up folder structure
        parent_folder_name = config.get('parent_folder_name', 'Sudan-MM-Submission-DefaultTeam')
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
        st.error(f"Failed to initialize APIs: {str(e)}")
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
        st.success("APIs initialized successfully!")
    
    # Sidebar with configuration info
    with st.sidebar:
        st.header("Configuration")
        st.info(f"**Team:** {config.get('team_name', 'N/A')}")
        st.info(f"**Spreadsheet:** {config.get('spreadsheet_name', 'N/A')}")
        st.info(f"**Parent Folder:** {config.get('parent_folder_name', 'N/A')}")
    
    # Main form
    with st.form("upload_form", clear_on_submit=True):
        st.header("Upload Multimodal Data")
        
        # Mode selector
        mode = st.radio(
            "Select Mode:",
            ["Image", "Video"],
            horizontal=True
        )
        
        # Media upload
        if mode == "Image":
            media_file = st.file_uploader(
                "Upload Image",
                type=['jpg', 'jpeg', 'png'],
                help="Upload a .jpg, .jpeg, or .png image file"
            )
        else:
            media_file = st.file_uploader(
                "Upload Video",
                type=['mp4'],
                help="Upload a .mp4 video file (3-10 seconds)"
            )
        
        # Audio upload
        audio_file = st.file_uploader(
            "Upload Audio Caption",
            type=['mp3'],
            help="Upload a .mp3 audio file (5-15 seconds)"
        )
        
        # Captions
        st.subheader("Captions")
        msa_caption = st.text_area(
            "MSA Caption (Modern Standard Arabic)",
            placeholder="Enter the Modern Standard Arabic caption...",
            height=100
        )
        sudanese_caption = st.text_area(
            "Sudanese Arabic Caption",
            placeholder="Enter the Sudanese Arabic caption...",
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
                            os.unlink(media_temp_path)
                            os.unlink(audio_temp_path)
                            return
                        
                        # Validate audio file format
                        is_valid, error_msg = validator.validate_audio_file(audio_temp_path)
                        if not is_valid:
                            st.error(f"Audio validation error: {error_msg}")
                            os.unlink(media_temp_path)
                            os.unlink(audio_temp_path)
                            return
                        
                        # Validate video duration
                        if mode == "Video":
                            is_valid, error_msg, duration = validator.validate_video_duration(
                                media_temp_path,
                                min_seconds=3.0,
                                max_seconds=10.0
                            )
                            if not is_valid:
                                st.error(f"Video validation error: {error_msg}")
                                os.unlink(media_temp_path)
                                os.unlink(audio_temp_path)
                                return
                        
                        # Validate audio duration
                        is_valid, error_msg, duration = validator.validate_audio_duration(
                            audio_temp_path,
                            min_seconds=5.0,
                            max_seconds=15.0
                        )
                        if not is_valid:
                            st.error(f"Audio validation error: {error_msg}")
                            os.unlink(media_temp_path)
                            os.unlink(audio_temp_path)
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
                        os.unlink(media_temp_path)
                        os.unlink(audio_temp_path)
                        
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
                        if 'media_temp_path' in locals() and os.path.exists(media_temp_path):
                            os.unlink(media_temp_path)
                        if 'audio_temp_path' in locals() and os.path.exists(audio_temp_path):
                            os.unlink(audio_temp_path)


if __name__ == "__main__":
    main()
