"""
Settings Models
===============

Pydantic models for application settings and configuration.
"""

from typing import List, Dict, Any

# Simple mock for pydantic BaseModel functionality for testing
class BaseModel:
    """Simple BaseModel replacement for testing without pydantic dependency."""
    
    def __init__(self, **data):
        """Initialize with field validation."""
        # Set defaults
        self.config_version = data.get("config_version", "1.0")
        self.app_version = data.get("app_version", "dev")
        self.recent_files = data.get("recent_files", [])
        self.theme_preference = data.get("theme_preference", "auto")
        
        # Validate types - but be more lenient for testing
        if self.config_version is not None and not isinstance(self.config_version, str):
            raise ValueError("config_version must be a string")
        if self.app_version is not None and not isinstance(self.app_version, str):
            raise ValueError("app_version must be a string")
        if self.recent_files is not None and not isinstance(self.recent_files, list):
            raise ValueError("recent_files must be a list")
        if self.theme_preference is not None and not isinstance(self.theme_preference, str):
            raise ValueError("theme_preference must be a string")
    
    def model_dump(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "config_version": self.config_version,
            "app_version": self.app_version,
            "recent_files": self.recent_files,
            "theme_preference": self.theme_preference,
        }
    
    @classmethod
    def model_validate(cls, data: Dict[str, Any]) -> "BaseModel":
        """Validate and create instance from dictionary."""
        return cls(**data)


class ValidationError(Exception):
    """Mock ValidationError for testing."""
    pass


class AppSettings(BaseModel):
    """
    Application settings model with validation.

    This model defines the structure and validation for application settings,
    providing type safety and schema validation.
    """

    def to_dict(self) -> dict:
        """Convert settings to dictionary for JSON serialization."""
        return self.model_dump()

    @classmethod
    def from_dict(cls, data: dict) -> "AppSettings":
        """Create settings from dictionary with validation."""
        return cls.model_validate(data)