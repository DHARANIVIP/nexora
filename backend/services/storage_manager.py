"""
Storage Manager Service
Handles all file storage operations for the new scan-based storage structure.
"""
import os
import shutil
from pathlib import Path
from typing import Dict, Optional
from loguru import logger
from backend.core.config import settings


class StorageManager:
    """Manages file storage for scan sessions"""
    
    @staticmethod
    def get_scan_paths(scan_id: str) -> Dict[str, Path]:
        """
        Get all storage paths for a given scan ID.
        
        Args:
            scan_id: Unique identifier for the scan
            
        Returns:
            Dictionary containing all relevant paths for the scan
        """
        scan_folder = settings.SCANS_FOLDER / scan_id
        
        return {
            "scan_folder": scan_folder,
            "video_path": scan_folder / "video",  # Extension added when saving
            "thumbnails_folder": scan_folder / "thumbnails",
            "processed_folder": scan_folder / "processed",
            "metadata_path": scan_folder / "metadata.json"
        }
    
    @staticmethod
    def create_scan_folder(scan_id: str) -> Dict[str, Path]:
        """
        Create folder structure for a new scan.
        
        Args:
            scan_id: Unique identifier for the scan
            
        Returns:
            Dictionary containing all created paths
        """
        paths = StorageManager.get_scan_paths(scan_id)
        
        # Create main scan folder
        paths["scan_folder"].mkdir(parents=True, exist_ok=True)
        
        # Create subfolders
        paths["thumbnails_folder"].mkdir(exist_ok=True)
        paths["processed_folder"].mkdir(exist_ok=True)
        
        logger.info(f"[{scan_id}] Created scan folder structure at {paths['scan_folder']}")
        return paths
    
    @staticmethod
    def save_video(scan_id: str, source_path: str, extension: str) -> Path:
        """
        Save uploaded video to scan folder.
        
        Args:
            scan_id: Unique identifier for the scan
            source_path: Path to the temporary uploaded file
            extension: File extension (e.g., '.mp4')
            
        Returns:
            Path where the video was saved
        """
        paths = StorageManager.get_scan_paths(scan_id)
        video_path = paths["scan_folder"] / f"video{extension}"
        
        # Move or copy the file
        if os.path.exists(source_path):
            shutil.move(source_path, str(video_path))
            logger.info(f"[{scan_id}] Saved video to {video_path}")
        
        return video_path
    
    @staticmethod
    def get_video_path(scan_id: str) -> Optional[Path]:
        """
        Get the path to the video file for a scan.
        Searches for video file with any supported extension.
        
        Args:
            scan_id: Unique identifier for the scan
            
        Returns:
            Path to video file if found, None otherwise
        """
        paths = StorageManager.get_scan_paths(scan_id)
        scan_folder = paths["scan_folder"]
        
        if not scan_folder.exists():
            return None
        
        # Look for video file with any extension
        for ext in settings.ALLOWED_EXTENSIONS:
            video_path = scan_folder / f"video{ext}"
            if video_path.exists():
                return video_path
        
        return None
    
    @staticmethod
    def get_thumbnails_folder(scan_id: str) -> Path:
        """Get the thumbnails folder path for a scan"""
        paths = StorageManager.get_scan_paths(scan_id)
        return paths["thumbnails_folder"]
    
    @staticmethod
    def get_processed_folder(scan_id: str) -> Path:
        """Get the processed frames folder path for a scan"""
        paths = StorageManager.get_scan_paths(scan_id)
        return paths["processed_folder"]
    
    @staticmethod
    def cleanup_scan(scan_id: str, keep_video: bool = True, keep_thumbnails: bool = True) -> None:
        """
        Clean up temporary files for a scan.
        
        Args:
            scan_id: Unique identifier for the scan
            keep_video: Whether to keep the original video file
            keep_thumbnails: Whether to keep thumbnail images
        """
        paths = StorageManager.get_scan_paths(scan_id)
        
        # Always delete processed frames folder
        if paths["processed_folder"].exists():
            shutil.rmtree(paths["processed_folder"])
            logger.info(f"[{scan_id}] Deleted processed frames folder")
        
        # Optionally delete thumbnails
        if not keep_thumbnails and paths["thumbnails_folder"].exists():
            shutil.rmtree(paths["thumbnails_folder"])
            logger.info(f"[{scan_id}] Deleted thumbnails folder")
        
        # Optionally delete video
        if not keep_video:
            video_path = StorageManager.get_video_path(scan_id)
            if video_path and video_path.exists():
                os.remove(video_path)
                logger.info(f"[{scan_id}] Deleted video file")
    
    @staticmethod
    def delete_scan(scan_id: str) -> bool:
        """
        Delete entire scan folder and all contents.
        
        Args:
            scan_id: Unique identifier for the scan
            
        Returns:
            True if deletion was successful, False otherwise
        """
        paths = StorageManager.get_scan_paths(scan_id)
        
        if paths["scan_folder"].exists():
            try:
                shutil.rmtree(paths["scan_folder"])
                logger.info(f"[{scan_id}] Deleted entire scan folder")
                return True
            except Exception as e:
                logger.error(f"[{scan_id}] Failed to delete scan folder: {e}")
                return False
        
        return False


# Create singleton instance
storage_manager = StorageManager()
