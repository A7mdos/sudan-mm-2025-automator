"""
Media validation module.
Handles validation of video and audio durations.
"""

import os
from typing import Tuple, Optional
from moviepy.editor import VideoFileClip
from pydub import AudioSegment


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
            video = VideoFileClip(file_path)
            duration = video.duration
            video.close()
            
            if duration < min_seconds:
                return False, f"Video duration ({duration:.2f}s) is less than minimum ({min_seconds}s)", duration
            if duration > max_seconds:
                return False, f"Video duration ({duration:.2f}s) exceeds maximum ({max_seconds}s)", duration
            
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
        try:
            audio = AudioSegment.from_file(file_path)
            duration = len(audio) / 1000.0  # Convert milliseconds to seconds
            
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
