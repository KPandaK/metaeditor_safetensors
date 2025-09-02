"""
Field Configuration Model - manages metadata field definitions and validation.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class FieldConfiguration:
    """Manages field definitions, validation rules, and UI configuration."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize field configuration.
        
        Args:
            config_path: Path to field_config.json. If None, uses default location.
        """
        self._config = {}
        self._tooltips = {}
        self._key_mappings = {}
        
        if config_path is None:
            # Default path relative to the config directory
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)), 
                'config', 
                'field_config.json'
            )
        
        self._load_configuration(config_path)
        self._load_legacy_config()
    
    def _load_configuration(self, config_path: str) -> None:
        """Load field configuration from JSON file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
            logger.info(f"Field configuration loaded from {config_path}")
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {config_path}")
            self._config = {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in configuration file: {e}")
            self._config = {}
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            self._config = {}
    
    def _load_legacy_config(self) -> None:
        """Load legacy configuration from config.py for backwards compatibility."""
        try:
            from config import MODELSPEC_TOOLTIPS, MODELSPEC_KEY_MAP
            self._tooltips = MODELSPEC_TOOLTIPS
            self._key_mappings = MODELSPEC_KEY_MAP
        except ImportError:
            logger.warning("Could not import legacy configuration")
    
    def get_field_names(self) -> list[str]:
        """Get list of all field names."""
        if self._config:
            return list(self._config.keys())
        else:
            # Fallback to legacy configuration
            return list(self._key_mappings.keys())
    
    def get_field_config(self, field_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific field.
        
        Args:
            field_name: Name of the field
            
        Returns:
            Dictionary containing field configuration
        """
        if field_name in self._config:
            return self._config[field_name]
        
        # Fallback for fields not in JSON config
        return {
            'widget_type': 'text_edit' if field_name == 'description' else 'line_edit',
            'tooltip': self._tooltips.get(field_name, ''),
            'max_length': 5000 if field_name == 'description' else 1000,
            'placeholder': f"Enter {field_name}..."
        }
    
    def get_metadata_key(self, field_name: str) -> str:
        """
        Get the metadata key for a field name.
        
        Args:
            field_name: Display name of the field
            
        Returns:
            Metadata key to use in safetensors file
        """
        return self._key_mappings.get(field_name, field_name)
    
    def get_tooltip(self, field_name: str) -> str:
        """Get tooltip text for a field."""
        if field_name in self._config:
            return self._config[field_name].get('tooltip', '')
        return self._tooltips.get(field_name, '')
    
    def get_validation_rules(self, field_name: str) -> Dict[str, Any]:
        """
        Get validation rules for a field.
        
        Returns:
            Dictionary containing validation rules
        """
        config = self.get_field_config(field_name)
        return {
            'required': config.get('required', False),
            'max_length': config.get('max_length', 1000),
            'min_length': config.get('min_length', 0),
            'pattern': config.get('pattern', None)
        }
    
    def validate_field_value(self, field_name: str, value: str) -> tuple[bool, list[str]]:
        """
        Validate a field value against its rules.
        
        Args:
            field_name: Name of the field
            value: Value to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        rules = self.get_validation_rules(field_name)
        
        # Required field check
        if rules['required'] and not value.strip():
            errors.append(f"{field_name.title()} is required")
        
        # Length checks
        if value and len(value) > rules['max_length']:
            errors.append(f"{field_name.title()} is too long ({len(value)} chars, max {rules['max_length']})")
        
        if value and len(value) < rules['min_length']:
            errors.append(f"{field_name.title()} is too short ({len(value)} chars, min {rules['min_length']})")
        
        # Pattern validation (if specified)
        if value and rules['pattern']:
            import re
            if not re.match(rules['pattern'], value):
                errors.append(f"{field_name.title()} format is invalid")
        
        return len(errors) == 0, errors
