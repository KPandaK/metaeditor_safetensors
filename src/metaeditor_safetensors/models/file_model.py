"""
File Model - represents a safetensors file and its properties.
"""

import os
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FileModel:
    """Represents a safetensors file with its properties."""
    
    def __init__(self, filepath: Optional[str] = None):
        """
        Initialize file model.
        
        Args:
            filepath: Path to the safetensors file
        """
        self._filepath = filepath
        self._file_size = 0
        self._last_modified = None
        self._is_valid = False
        
        if filepath:
            self._load_file_info()
    
    def _load_file_info(self) -> None:
        """Load file information from the filesystem."""
        if not self._filepath or not os.path.exists(self._filepath):
            self._is_valid = False
            return
        
        try:
            stat = os.stat(self._filepath)
            self._file_size = stat.st_size
            self._last_modified = datetime.fromtimestamp(stat.st_mtime)
            self._is_valid = self._validate_file()
        except Exception as e:
            logger.error(f"Error loading file info for {self._filepath}: {e}")
            self._is_valid = False
    
    def _validate_file(self) -> bool:
        """
        Validate that the file is a proper safetensors file.
        
        Returns:
            True if file appears to be valid safetensors format
        """
        if not self._filepath or not os.path.exists(self._filepath):
            return False
        
        try:
            # Basic validation - check file extension and minimum size
            if not self._filepath.lower().endswith('.safetensors'):
                return False
            
            # File should be at least large enough for header length (8 bytes)
            if self._file_size < 8:
                return False
            
            # Try to read header to verify format
            with open(self._filepath, 'rb') as f:
                header_len_bytes = f.read(8)
                if len(header_len_bytes) != 8:
                    return False
                
                header_len = int.from_bytes(header_len_bytes, 'little')
                
                # Header length should be reasonable
                if header_len <= 0 or header_len > self._file_size:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating file {self._filepath}: {e}")
            return False
    
    @property
    def filepath(self) -> Optional[str]:
        """Get the file path."""
        return self._filepath
    
    @property
    def filename(self) -> str:
        """Get just the filename without path."""
        if self._filepath:
            return os.path.basename(self._filepath)
        return "No file selected"
    
    @property
    def file_size(self) -> int:
        """Get file size in bytes."""
        return self._file_size
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in MB."""
        return self._file_size / (1024 * 1024)
    
    @property
    def last_modified(self) -> Optional[datetime]:
        """Get last modified timestamp."""
        return self._last_modified
    
    @property
    def is_valid(self) -> bool:
        """Check if the file is valid."""
        return self._is_valid
    
    @property
    def exists(self) -> bool:
        """Check if the file exists."""
        return self._filepath is not None and os.path.exists(self._filepath)
    
    def set_filepath(self, filepath: str) -> None:
        """
        Set a new file path and reload file info.
        
        Args:
            filepath: New file path
        """
        self._filepath = filepath
        self._load_file_info()
    
    def reload(self) -> None:
        """Reload file information from filesystem."""
        if self._filepath:
            self._load_file_info()
    
    def __str__(self) -> str:
        """String representation of the file model."""
        if self._filepath:
            return f"FileModel({self.filename}, {self.file_size_mb:.1f}MB, valid={self.is_valid})"
        return "FileModel(no file)"
    
    def __repr__(self) -> str:
        """Detailed representation of the file model."""
        return (f"FileModel(filepath='{self._filepath}', "
                f"size={self._file_size}, "
                f"valid={self._is_valid})")
