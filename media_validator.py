"""
Media validation module.
Handles validation of video and audio durations using ffmpeg-python.
"""

import os
import subprocess
import json
from typing import Tuple, Optional


class MediaValidator:
    """Class for validating media file durations."""
    
    @staticmethod
    def _get_media_duration_ffprobe(file_path: str) -> Optional[float]:
        """
        Get media duration using ffprobe (part of ffmpeg).
        
        Args:
            file_path: Path to the media file
            
        Returns:
            Duration in seconds, or None if error
        """
        try:
            # Use ffprobe to get duration
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'json',
                file_path
            ]
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration_str = data.get('format', {}).get('duration')
                if duration_str:
                    return float(duration_str)
            
            return None
            
        except (subprocess.TimeoutExpired, subprocess.SubprocessError, json.JSONDecodeError, ValueError):
            return None
        except FileNotFoundError:
            # ffprobe not found
            return None
    
    @staticmethod
    def validate_video_duration(file_path: str, min_seconds: float = 3.0, max_seconds: float = 10.0) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Validate video duration using ffprobe.
        
        Args:
            file_path: Path to the video file
            min_seconds: Minimum allowed duration in seconds
            max_seconds: Maximum allowed duration in seconds
            
        Returns:
            Tuple of (is_valid, error_message, duration)
        """
        # First check if ffprobe is available
        try:
            subprocess.run(['ffprobe', '-version'], 
                         stdout=subprocess.PIPE, 
                         stderr=subprocess.PIPE,
                         timeout=5)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False, (
                "ffprobe (part of ffmpeg) is not installed or not in PATH. "
                "Please install ffmpeg:\n"
                "- Windows: Download from https://ffmpeg.org/download.html or use 'choco install ffmpeg'\n"
                "- Mac: brew install ffmpeg\n"
                "- Linux: sudo apt-get install ffmpeg"
            ), None
        
        try:
            duration = MediaValidator._get_media_duration_ffprobe(file_path)
            
            if duration is None:
                return False, "Could not read video duration. The file may be corrupted.", None
            
            if duration < min_seconds:
                return False, f"Video duration ({duration:.2f}s) is less than minimum ({min_seconds}s)", duration
            elif duration > max_seconds:
                return False, f"Video duration ({duration:.2f}s) exceeds maximum ({max_seconds}s)", duration
            else:
                return True, None, duration
                
        except Exception as e:
            return False, f"Error reading video file: {str(e)}", None
    
    @staticmethod
    def validate_audio_duration(file_path: str, min_seconds: float = 5.0, max_seconds: float = 15.0) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Validate audio duration.
        
        Args:
            file_path: Path to the audio file
            min_seconds: Minimum allowed duration in seconds
            max_seconds: Maximum allowed duration in seconds
            
        Returns:
            Tuple of (is_valid, error_message, duration)
        """
        # Try mutagen first (pure Python, no ffmpeg required for MP3)
        try:
            from mutagen.mp3 import MP3
            from mutagen import File
            
            audio_file = File(file_path)
            if audio_file is not None:
                duration = audio_file.info.length
                
                if duration < min_seconds:
                    return False, f"Audio duration ({duration:.2f}s) is less than minimum ({min_seconds}s)", duration
                if duration > max_seconds:
                    return False, f"Audio duration ({duration:.2f}s) exceeds maximum ({max_seconds}s)", duration
                
                return True, None, duration
        except ImportError:
            # Fallback to ffprobe if mutagen is not available
            pass
        except Exception as e:
            # If mutagen fails, try ffprobe as fallback
            pass
        
        # Fallback to ffprobe
        try:
            duration = MediaValidator._get_media_duration_ffprobe(file_path)
            
            if duration is None:
                return False, (
                    "Could not read audio duration. Please install mutagen (pip install mutagen) "
                    "or ensure ffmpeg is installed on your system."
                ), None
            
            if duration < min_seconds:
                return False, f"Audio duration ({duration:.2f}s) is less than minimum ({min_seconds}s)", duration
            if duration > max_seconds:
                return False, f"Audio duration ({duration:.2f}s) exceeds maximum ({max_seconds}s)", duration
            
            return True, None, duration
            
        except Exception as e:
            return False, f"Error reading audio file: {str(e)}", None
    
    @staticmethod
    def validate_media_file(file_path: str, file_type: str) -> Tuple[bool, Optional[str]]:
        """
        Validate media file extension.
        
        Args:
            file_path: Path to the file
            file_type: Either 'image' or 'video'
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if file_type == 'image':
            valid_extensions = ['.jpg', '.jpeg', '.png']
            if ext not in valid_extensions:
                return False, f"Invalid image format. Allowed: {', '.join(valid_extensions)}"
        elif file_type == 'video':
            if ext != '.mp4':
                return False, "Invalid video format. Only .mp4 is allowed"
        else:
            return False, f"Unknown file type: {file_type}"
        
        return True, None
    
    @staticmethod
    def validate_audio_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Validate audio file extension.
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not os.path.exists(file_path):
            return False, "File does not exist"
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext != '.mp3':
            return False, "Invalid audio format. Only .mp3 is allowed"
        
        return True, None
