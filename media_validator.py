"""
Media validation module.
Handles validation of video and audio durations.
"""

import os
from typing import Tuple, Optional


class MediaValidator:
    """Class for validating media file durations."""
    
    @staticmethod
    def validate_video_duration(file_path: str, min_seconds: float = 3.0, max_seconds: float = 10.0) -> Tuple[bool, Optional[str], Optional[float]]:
        """
        Validate video duration.
        
        Args:
            file_path: Path to the video file
            min_seconds: Minimum allowed duration in seconds
            max_seconds: Maximum allowed duration in seconds
            
        Returns:
            Tuple of (is_valid, error_message, duration)
        """
        try:
            from moviepy.editor import VideoFileClip
        except ImportError:
            return False, "moviepy library is not installed. Please install it with: pip install moviepy", None
        
        video = None
        try:
            video = VideoFileClip(file_path)
            duration = video.duration
            
            if duration < min_seconds:
                result = (False, f"Video duration ({duration:.2f}s) is less than minimum ({min_seconds}s)", duration)
            elif duration > max_seconds:
                result = (False, f"Video duration ({duration:.2f}s) exceeds maximum ({max_seconds}s)", duration)
            else:
                result = (True, None, duration)
            
            # Ensure video is closed before returning
            if video:
                video.close()
                video = None
            
            return result
        except Exception as e:
            # Make sure to close video even on error
            if video:
                try:
                    video.close()
                except:
                    pass
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
            # Fallback to pydub if mutagen is not available
            pass
        except Exception as e:
            # If mutagen fails, try pydub as fallback
            pass
        
        # Fallback to pydub
        try:
            from pydub import AudioSegment
            
            audio = AudioSegment.from_file(file_path)
            duration = len(audio) / 1000.0  # Convert milliseconds to seconds
            
            if duration < min_seconds:
                return False, f"Audio duration ({duration:.2f}s) is less than minimum ({min_seconds}s)", duration
            if duration > max_seconds:
                return False, f"Audio duration ({duration:.2f}s) exceeds maximum ({max_seconds}s)", duration
            
            return True, None, duration
        except ImportError:
            return False, "Neither mutagen nor pydub library is installed. Please install one with: pip install mutagen (recommended) or pip install pydub", None
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
