"""
Theme Management Service
========================

Service for managing application themes with qt-material integration,
system theme detection, user preferences, and runtime theme switching.
"""

import logging
import platform
from typing import Optional, List, Dict, Any, Literal
from enum import Enum

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QObject, Signal

import qt_material
import darkdetect

logger = logging.getLogger(__name__)

class SystemTheme(Enum):
    """System theme preference enumeration."""
    LIGHT = "light"
    DARK = "dark"
    UNKNOWN = "unknown"

class ThemeCategory(Enum):
    """Theme category enumeration."""
    AUTO = "auto"      # Follow system theme
    LIGHT = "light"    # Light themes
    DARK = "dark"      # Dark themes
    CUSTOM = "custom"  # Custom/legacy themes

class MaterialTheme:
    """Represents a qt-material theme."""
    
    def __init__(self, filename: str, display_name: str, category: ThemeCategory, 
                 invert_secondary: bool = False):
        self.filename = filename
        self.display_name = display_name
        self.category = category
        self.invert_secondary = invert_secondary
    
    def __str__(self):
        return f"{self.display_name} ({self.filename})"
    
    def __repr__(self):
        return f"MaterialTheme('{self.filename}', '{self.display_name}', {self.category})"

class ThemeService(QObject):
    """
    Service for managing application themes.
    
    Integrates qt-material themes with system theme detection and provides
    runtime theme switching capabilities.
    """
    
    # Signals
    theme_changed = Signal(str)  # Emitted when theme changes, passes theme filename
    
    def __init__(self, app: QApplication, config_service=None):
        super().__init__()
        self._app = app
        self._config_service = config_service
        self._cached_system_theme: Optional[SystemTheme] = None
        self._current_theme: Optional[MaterialTheme] = None
        self._available_themes: Dict[str, MaterialTheme] = {}
        
        # Initialize available themes
        self._initialize_themes()
        
        logger.info("ThemeService initialized")
    
    def _initialize_themes(self):
        """Initialize the available theme catalog."""
        logger.debug("Initializing theme catalog")
        
        # Get available themes from qt-material
        try:
            theme_list = qt_material.list_themes()
            logger.debug(f"Found {len(theme_list)} qt-material themes")
        except Exception as e:
            logger.error(f"Error getting qt-material themes: {e}")
            theme_list = []
        
        # Categorize and create MaterialTheme objects
        for theme_file in theme_list:
            theme = self._create_material_theme(theme_file)
            if theme:
                self._available_themes[theme.filename] = theme
        
        logger.info(f"Initialized {len(self._available_themes)} themes")
    
    def _create_material_theme(self, filename: str) -> Optional[MaterialTheme]:
        """Create a MaterialTheme object from a filename."""
        if not filename.endswith('.xml'):
            return None
        
        # Parse theme name and category
        name_base = filename[:-4]  # Remove .xml extension
        
        if name_base.startswith('dark_'):
            color = name_base[5:]  # Remove 'dark_' prefix
            display_name = f"Dark {color.replace('_', ' ').title()}"
            category = ThemeCategory.DARK
            invert_secondary = False
        elif name_base.startswith('light_'):
            color = name_base[6:]  # Remove 'light_' prefix
            display_name = f"Light {color.replace('_', ' ').title()}"
            category = ThemeCategory.LIGHT
            invert_secondary = True
        else:
            # Handle any other themes
            display_name = name_base.replace('_', ' ').title()
            category = ThemeCategory.CUSTOM
            invert_secondary = False
        
        return MaterialTheme(filename, display_name, category, invert_secondary)
    
    def _detect_system_theme(self, use_cache: bool = True) -> SystemTheme:
        """
        Detect the current system theme preference.
        
        Args:
            use_cache: If True, return cached result if available
            
        Returns:
            SystemTheme enum value (LIGHT, DARK, or UNKNOWN)
        """
        if use_cache and self._cached_system_theme is not None:
            return self._cached_system_theme
        
        try:
            # Use darkdetect to detect system theme
            theme_str = darkdetect.theme()
            
            if theme_str is None:
                logger.warning("darkdetect returned None, theme detection failed")
                theme = SystemTheme.UNKNOWN
            elif theme_str.lower() == "dark":
                theme = SystemTheme.DARK
            elif theme_str.lower() == "light":
                theme = SystemTheme.LIGHT
            else:
                logger.warning(f"darkdetect returned unexpected value: {theme_str}")
                theme = SystemTheme.UNKNOWN
                
        except Exception as e:
            logger.error(f"Error detecting system theme: {e}")
            theme = SystemTheme.UNKNOWN
        
        self._cached_system_theme = theme
        logger.info(f"Detected system theme: {theme.value}")
        return theme
    
    def _clear_system_theme_cache(self):
        """Clear the cached system theme detection result."""
        self._cached_system_theme = None
        logger.debug("System theme detection cache cleared")
    
    def _get_platform_info(self) -> dict:
        """
        Get platform information for debugging.
        
        Returns:
            Dictionary with platform information
        """
        return {
            "platform": platform.system().lower(),
            "platform_detailed": platform.platform(),
            "python_version": platform.python_version(),
            "darkdetect_available": True,  # We imported it successfully
        }
    
    def get_available_themes(self) -> Dict[str, MaterialTheme]:
        """Get all available themes."""
        return self._available_themes.copy()
    
    def get_themes_by_category(self, category: ThemeCategory) -> List[MaterialTheme]:
        """Get themes filtered by category."""
        return [theme for theme in self._available_themes.values() 
                if theme.category == category]
    
    def get_theme_categories(self) -> List[ThemeCategory]:
        """Get all available theme categories."""
        categories = set(theme.category for theme in self._available_themes.values())
        categories.add(ThemeCategory.AUTO)  # Always include auto
        return sorted(categories, key=lambda x: x.value)
    
    def get_current_theme(self) -> Optional[MaterialTheme]:
        """Get the currently applied theme."""
        return self._current_theme
    
    def apply_theme(self, theme_identifier: str, save_preference: bool = True) -> bool:
        """
        Apply a theme to the application.
        
        Args:
            theme_identifier: Theme filename, 'auto', 'system_light', or 'system_dark'
            save_preference: Whether to save this choice to config
            
        Returns:
            True if theme was applied successfully
        """
        logger.debug(f"Applying theme: {theme_identifier}")
        
        try:
            if theme_identifier == 'auto':
                return self._apply_auto_theme(save_preference)
            elif theme_identifier == 'system_light':
                return self._apply_default_light_theme(save_preference)
            elif theme_identifier == 'system_dark':
                return self._apply_default_dark_theme(save_preference)
            else:
                theme = self._available_themes.get(theme_identifier)
                if not theme:
                    logger.error(f"Theme not found: {theme_identifier}")
                    return False
                
                return self._apply_material_theme(theme, save_preference)
        
        except Exception as e:
            logger.error(f"Error applying theme {theme_identifier}: {e}")
            return False
    
    def _apply_auto_theme(self, save_preference: bool = True) -> bool:
        """Apply theme based on system preference."""
        system_theme = self._detect_system_theme()
        
        if system_theme == SystemTheme.DARK:
            default_theme = self._get_default_dark_theme()
        else:
            default_theme = self._get_default_light_theme()
        
        if default_theme:
            success = self._apply_material_theme(default_theme, False)  # Don't save individual theme
            if success and save_preference and self._config_service:
                self._config_service.set_theme_preference('auto')
            return success
        
        return False
    
    def _apply_default_light_theme(self, save_preference: bool = True) -> bool:
        """Apply the default light theme."""
        theme = self._get_default_light_theme()
        if theme:
            return self._apply_material_theme(theme, save_preference)
        return False
    
    def _apply_default_dark_theme(self, save_preference: bool = True) -> bool:
        """Apply the default dark theme."""
        theme = self._get_default_dark_theme()
        if theme:
            return self._apply_material_theme(theme, save_preference)
        return False
    
    def _get_default_light_theme(self) -> Optional[MaterialTheme]:
        """Get the default light theme."""
        # Prefer light_blue, fallback to first available light theme
        preferred = ['light_blue.xml', 'light_cyan.xml', 'light_teal.xml']
        
        for filename in preferred:
            if filename in self._available_themes:
                return self._available_themes[filename]
        
        # Fallback to any light theme
        light_themes = self.get_themes_by_category(ThemeCategory.LIGHT)
        return light_themes[0] if light_themes else None
    
    def _get_default_dark_theme(self) -> Optional[MaterialTheme]:
        """Get the default dark theme."""
        # Prefer dark_teal, fallback to first available dark theme
        preferred = ['dark_teal.xml', 'dark_blue.xml', 'dark_cyan.xml']
        
        for filename in preferred:
            if filename in self._available_themes:
                return self._available_themes[filename]
        
        # Fallback to any dark theme
        dark_themes = self.get_themes_by_category(ThemeCategory.DARK)
        return dark_themes[0] if dark_themes else None
    
    def _apply_material_theme(self, theme: MaterialTheme, save_preference: bool = True) -> bool:
        """Apply a qt-material theme."""
        try:
            logger.debug(f"Applying material theme: {theme}")
            
            # Apply the theme using qt-material
            qt_material.apply_stylesheet(
                self._app, 
                theme=theme.filename,
                invert_secondary=theme.invert_secondary
            )
            
            self._current_theme = theme
            
            # Save preference if requested
            if save_preference and self._config_service:
                self._config_service.set_theme_preference(theme.filename)
            
            # Emit signal
            self.theme_changed.emit(theme.filename)
            
            logger.info(f"Successfully applied theme: {theme.display_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error applying material theme {theme}: {e}")
            return False
    
    def apply_user_preference(self) -> bool:
        """
        Apply theme based on user preference from config.
        
        Returns:
            True if theme was applied successfully
        """
        if not self._config_service:
            logger.warning("No config service available, applying auto theme")
            return self._apply_auto_theme(False)
        
        try:
            preferred_theme = self._config_service.get_theme_preference()
            if preferred_theme:
                return self.apply_theme(preferred_theme, False)  # Don't re-save
            else:
                logger.debug("No theme preference found, applying auto theme")
                return self._apply_auto_theme(True)  # Save the auto preference
        
        except Exception as e:
            logger.error(f"Error applying user preference: {e}")
            return self._apply_auto_theme(True)
    
    def refresh_system_theme(self) -> bool:
        """
        Refresh system theme detection and re-apply auto theme if currently using it.
        
        Returns:
            True if refresh was successful
        """
        self._clear_system_theme_cache()
        
        # If current preference is auto, re-apply it
        if (self._config_service and 
            self._config_service.get_theme_preference() == 'auto'):
            return self._apply_auto_theme(False)
        
        return True
    
    def get_theme_info(self) -> Dict[str, Any]:
        """
        Get comprehensive theme information for debugging.
        
        Returns:
            Dictionary with theme information
        """
        current_theme_info = None
        if self._current_theme:
            current_theme_info = {
                'filename': self._current_theme.filename,
                'display_name': self._current_theme.display_name,
                'category': self._current_theme.category.value,
                'invert_secondary': self._current_theme.invert_secondary
            }
        
        return {
            'current_theme': current_theme_info,
            'available_themes': len(self._available_themes),
            'system_theme': self._detect_system_theme().value,
            'user_preference': (self._config_service.get_theme_preference() 
                              if self._config_service else None),
            'categories': [cat.value for cat in self.get_theme_categories()],
            'platform_info': self._get_platform_info()
        }
