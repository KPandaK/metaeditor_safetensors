"""
Theme Management Service
========================

Service for managing application themes with modular QSS files,
system theme detection, user preferences, and runtime theme switching.
"""

import glob
import logging
import os
from enum import Enum
from importlib import resources
from pathlib import Path
from typing import Any, Dict, List, Optional

import darkdetect
import yaml
from PySide6.QtCore import QFile, QFileSystemWatcher, QIODevice, QObject, Signal
from PySide6.QtWidgets import QApplication

from .file_service import get_project_root

logger = logging.getLogger(__name__)


class SystemTheme(Enum):
    """System theme preference enumeration."""

    LIGHT = "light"
    DARK = "dark"
    UNKNOWN = "unknown"


class ThemeCategory(Enum):
    """Theme category enumeration."""

    AUTO = "auto"  # Use system theme
    LIGHT = "light"  # Light theme
    DARK = "dark"  # Dark theme


class Theme:
    """Represents a modular QSS theme configuration."""

    def __init__(
        self,
        theme_id: str,
        display_name: str,
        category: ThemeCategory,
        theme_directory: Optional[str] = None,
    ):
        self.theme_id = theme_id
        self.display_name = display_name
        self.category = category
        self.theme_directory = theme_directory

        # Optional metadata (set by theme loading)
        self.description: Optional[str] = None
        self.version: Optional[str] = None
        self.qss_order: List[str] = []
        self.settings: Dict[str, Any] = {}

    def __str__(self):
        return f"{self.display_name} ({self.theme_id})"

    def __repr__(self):
        return f"Theme('{self.theme_id}', '{self.display_name}', {self.category})"


class ThemeService(QObject):
    """
    Service for managing application themes with modular QSS files.

    Supports theme directories containing multiple QSS files that are
    combined at runtime, with system theme detection and live reloading
    in development mode.
    """

    # Signals
    theme_changed = Signal(str)

    def __init__(self, app: QApplication, config_service=None):
        super().__init__()
        self._app = app
        self._config_service = config_service
        self._cached_system_theme: Optional[SystemTheme] = None
        self._current_theme: Optional[Theme] = None
        self._available_themes: Dict[str, Theme] = {}

        # Development mode settings
        # Use file service to find development themes directory
        try:
            project_root = get_project_root()
            self._dev_themes_root = project_root / "assets" / "themes"
        except Exception:
            logger.warning("Could not determine project root for themes directory")

        self._enable_live_reload = (
            os.getenv("DEV_LIVE_STYLING", "false").lower() == "true"
        )
        
        self._file_watcher: Optional[QFileSystemWatcher] = None
        self._watched_files: List[str] = []

        # Initialize available themes
        self._initialize_themes()

        # Setup file watching if in development mode
        if self._enable_live_reload:
            self._setup_file_watcher()

        mode = "dev" if self._enable_live_reload else "prod"
        logger.info(f"ThemeService initialized in {mode} mode")

    def _initialize_themes(self):
        """Find the available themes"""
        logger.debug("Searching for themes")

        # Auto theme (follows system)
        auto_theme = Theme("auto", "Auto (Use System)", ThemeCategory.AUTO, None)
        self._available_themes["auto"] = auto_theme

        # Scan for themes based on mode
        if self._enable_live_reload:
            self._scan_themes_from_filesystem()
        else:
            self._scan_themes_from_resource()

        logger.info(
            f"Initialized {len(self._available_themes)} themes: {list(self._available_themes.keys())}"
        )

    def _scan_themes_from_filesystem(self):
        """Scan filesystem for theme directories (development mode)."""
        if not self._dev_themes_root.exists():
            logger.warning(
                f"Development themes directory not found: {self._dev_themes_root}"
            )
            return

        for theme_dir in self._dev_themes_root.iterdir():
            if theme_dir.is_dir():
                try:
                    theme = self._load_theme(theme_dir.name, str(theme_dir))
                    self._available_themes[theme.theme_id] = theme
                    logger.debug(f"Found filesystem theme: {theme}")
                except Exception as e:
                    logger.warning(f"Failed to load theme from {theme_dir}: {e}")

    def _scan_themes_from_resource(self):
        """Scan Qt resources for themes (production mode)."""
        registry = self._load_themes_registry()

        if not registry or "themes" not in registry:
            logger.warning("No themes registry found or registry is empty")
            return

        for theme_id, theme_info in registry["themes"].items():
            try:
                theme_path = f":/themes/{theme_id}"
                theme = self._load_theme(theme_id, theme_path, theme_info)
                self._available_themes[theme_id] = theme
                logger.debug(f"Found resource theme: {theme}")
            except Exception as e:
                logger.warning(f"Failed to load theme {theme_id} from resources: {e}")

    def _load_themes_registry(self) -> Optional[dict]:
        try:
            package_files = resources.files("metaeditor_safetensors")
            registry_file = package_files / "themes_registry.yaml"

            if registry_file.is_file():
                with registry_file.open("r", encoding="utf-8") as f:
                    registry = yaml.safe_load(f)
                    logger.debug("Loaded registry from package resources")
                    return registry
            else:
                logger.warning("Registry not found in package resources")
                return None

        except Exception as e:
            logger.error(f"Error loading registry: {e}")
            return None                

    def _load_theme(self, theme_id: str, theme_path: str, registry_info: Optional[dict] = None) -> Theme:
        """
        Load a theme from either filesystem or Qt resources.
        
        Args:
            theme_id: Theme identifier
            theme_path: Path to theme (filesystem directory or Qt resource path like :/themes/dark)
            registry_info: Optional registry metadata for resource themes
            
        Returns:
            Theme object with configuration loaded
        """
        # Set defaults based on theme_id and registry info
        if registry_info:
            display_name = registry_info.get("name", theme_id.replace("_", " ").title())
            description = registry_info.get("description", f"Theme: {display_name}")
            version = registry_info.get("version", "1.0.0")
            category_str = registry_info.get("category", theme_id)
        else:
            display_name = theme_id.replace("_", " ").title()
            description = f"Theme: {display_name}"
            version = "1.0.0"
            category_str = theme_id

        # Special handling for built-in theme names
        if theme_id == "dark":
            display_name = "Dark"
            category = ThemeCategory.DARK
        elif theme_id == "light":
            display_name = "Light"
            category = ThemeCategory.LIGHT
        else:
            # Determine category from registry or theme name
            if category_str == "dark":
                category = ThemeCategory.DARK
            elif category_str == "light":
                category = ThemeCategory.LIGHT
            else:
                category = ThemeCategory.DARK

        qss_order = []
        settings = {}

        # Try to load YAML configuration
        config = self._load_yaml_config(theme_id, theme_path, registry_info)
        if config:
            display_name = config.get("name", display_name)
            description = config.get("description", description)
            version = config.get("version", version)
            qss_order = config.get("qss_order", [])
            settings = config.get("settings", {})

            # Override category if specified in config
            config_category = config.get("category", "").lower()
            if config_category == "light":
                category = ThemeCategory.LIGHT
            elif config_category == "dark":
                category = ThemeCategory.DARK

        # Create and return theme object
        theme = Theme(
            theme_id=theme_id,
            display_name=display_name,
            category=category,
            theme_directory=theme_path,
        )
        
        theme.description = description
        theme.version = version
        theme.qss_order = qss_order
        theme.settings = settings
        
        return theme

    def _load_yaml_config(self, theme_id: str, theme_path: str, registry_info: Optional[dict] = None) -> Optional[dict]:
        """Load YAML configuration from filesystem or Qt resources."""
        if theme_path.startswith(":/"):
            # Qt resource path
            config_file = registry_info.get("config_file", f"{theme_id}.yaml") if registry_info else f"{theme_id}.yaml"
            config_paths = [
                f"{theme_path}/{config_file}",
                f"{theme_path}/{theme_id}.yaml",
                f"{theme_path}/{theme_id}.yml", 
                f"{theme_path}/theme.yaml",
                f"{theme_path}/theme.yml",
            ]
            
            for resource_path in config_paths:
                qfile = QFile(resource_path)
                if qfile.open(QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text):
                    try:
                        content = bytes(qfile.readAll().data()).decode("utf-8")
                        config = yaml.safe_load(content)
                        qfile.close()
                        
                        if config:
                            logger.debug(f"Loaded theme config from resources: {resource_path}")
                            return config
                            
                    except Exception as e:
                        logger.warning(f"Could not load theme config from {resource_path}: {e}")
                    finally:
                        qfile.close()
        else:
            # Filesystem path
            theme_dir = Path(theme_path)
            config_files = [
                theme_dir / f"{theme_id}.yaml",
                theme_dir / f"{theme_id}.yml",
                theme_dir / "theme.yaml", 
                theme_dir / "theme.yml",
            ]
            
            for config_file in config_files:
                if config_file.exists():
                    try:
                        with open(config_file, "r", encoding="utf-8") as f:
                            config = yaml.safe_load(f)
                        
                        if config:
                            logger.debug(f"Loaded theme config from filesystem: {config_file}")
                            return config
                            
                    except Exception as e:
                        logger.warning(f"Could not load theme config from {config_file}: {e}")
        
        return None

    def _discover_qss_files(self, theme: Theme) -> List[str]:
        """
        Discover all QSS files in a theme directory, respecting the configured order.
        Handles both filesystem paths (development) and Qt resource paths (production).

        Args:
            theme: Theme object with directory and ordering information

        Returns:
            List of QSS file paths sorted according to theme configuration
        """
        if not theme.theme_directory:
            return []

        ordered_files = []

        if theme.theme_directory.startswith(":/"):
            # Qt resource path (production mode)
            # We can't scan resource directories, so use the configured order
            for filename in theme.qss_order:
                resource_path = f"{theme.theme_directory}/{filename}"
                qss_file = QFile(resource_path)
                if qss_file.exists():
                    ordered_files.append(resource_path)
                else:
                    logger.warning(f"QSS file not found in resources: {resource_path}")
        else:
            # Filesystem path (development mode)
            theme_path = Path(theme.theme_directory)
            if not (theme_path.exists() and theme_path.is_dir()):
                return []

            # Find all .qss files in the theme directory
            all_qss_files = set(theme_path.glob("*.qss"))

            # First, add files in the specified order
            for filename in theme.qss_order:
                qss_file = theme_path / filename
                if qss_file in all_qss_files:
                    ordered_files.append(str(qss_file))
                    all_qss_files.remove(qss_file)

            # Then add any remaining files alphabetically
            remaining_files = sorted([str(f) for f in all_qss_files])
            ordered_files.extend(remaining_files)

        logger.debug(
            f"QSS file order for {theme.theme_id}: {[Path(f).name for f in ordered_files]}"
        )
        return ordered_files

    def _combine_qss_files(self, qss_files: List[str]) -> str:
        """
        Combine multiple QSS files into a single stylesheet.
        Handles both filesystem paths and Qt resource paths.

        Args:
            qss_files: List of QSS file paths to combine

        Returns:
            Combined QSS content as string
        """
        combined_qss = []

        for qss_file in qss_files:
            try:
                content = ""
                file_name = Path(qss_file).name

                if qss_file.startswith(":/"):
                    # Qt resource path (production mode)
                    qss_resource = QFile(qss_file)
                    if qss_resource.open(
                        QIODevice.OpenModeFlag.ReadOnly | QIODevice.OpenModeFlag.Text
                    ):
                        content = bytes(qss_resource.readAll().data()).decode("utf-8")
                        qss_resource.close()
                        logger.debug(f"Loaded QSS from resources: {qss_file}")
                    else:
                        logger.warning(
                            f"Could not load QSS file from resources: {qss_file}"
                        )
                        continue

                elif self._enable_live_reload and os.path.exists(qss_file):
                    # Development mode: read from filesystem
                    with open(qss_file, "r", encoding="utf-8") as f:
                        content = f.read()
                        logger.debug(f"Loaded QSS from filesystem: {qss_file}")
                else:
                    logger.warning(f"QSS file not accessible: {qss_file}")
                    continue

                if content:
                    combined_qss.append(f"/* From: {file_name} */\n{content}")

            except Exception as e:
                logger.error(f"Error loading QSS file {qss_file}: {e}")

        combined_content = "\n\n".join(combined_qss)
        logger.debug(
            f"Combined {len(qss_files)} QSS files into {len(combined_content)} characters"
        )
        return combined_content

    def _load_theme_qss(self, theme: Theme) -> str:
        """
        Load and combine QSS files for a theme.

        Args:
            theme: Theme object to load QSS for

        Returns:
            Combined QSS content as string
        """
        if theme.theme_id == "auto":
            # For auto theme, determine which theme to use based on system
            system_theme = self._detect_system_theme()
            if system_theme == SystemTheme.LIGHT:
                fallback_theme = self._available_themes.get("light")
            else:
                fallback_theme = self._available_themes.get("dark")

            if fallback_theme and fallback_theme.theme_directory:
                qss_files = self._discover_qss_files(fallback_theme)
                return self._combine_qss_files(qss_files)
            else:
                logger.warning("No fallback theme available for auto theme")
                return ""

        if not theme.theme_directory:
            logger.warning(f"No theme directory specified for theme: {theme.theme_id}")
            return ""

        qss_files = self._discover_qss_files(theme)
        return self._combine_qss_files(qss_files)

    def _setup_file_watcher(self):
        """Setup file watching for live reload in development mode."""
        if not self._enable_live_reload:
            return

        # Watch all QSS files in all theme directories
        watch_files = []

        for theme in self._available_themes.values():
            if theme.theme_directory:
                qss_files = self._discover_qss_files(theme)
                watch_files.extend(qss_files)

        if watch_files:
            self._file_watcher = QFileSystemWatcher(watch_files)
            self._file_watcher.fileChanged.connect(self._on_theme_file_changed)
            self._watched_files = watch_files
            logger.info(
                f"Live theme reloading enabled, watching {len(watch_files)} files"
            )

    def _on_theme_file_changed(self, file_path: str):
        """Handle theme file changes for live reloading."""
        logger.debug(f"Theme file changed: {file_path}, reloading...")
        if self._current_theme:
            # Re-apply the current theme to pick up CSS changes
            self._apply_theme_internal(self._current_theme, save_preference=False)

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
        import platform

        return {
            "platform": platform.system().lower(),
            "platform_detailed": platform.platform(),
            "python_version": platform.python_version(),
            "darkdetect_available": True,  # We imported it successfully
            "theme_service_version": "2.0.0-modular",
        }

    def get_available_themes(self) -> Dict[str, Theme]:
        """Get all available themes."""
        return self._available_themes.copy()

    def get_themes_by_category(self, category: ThemeCategory) -> List[Theme]:
        """Get themes filtered by category."""
        return [
            theme
            for theme in self._available_themes.values()
            if theme.category == category
        ]

    def get_theme_categories(self) -> List[ThemeCategory]:
        """Get all available theme categories."""
        return list(ThemeCategory)

    def get_current_theme(self) -> Optional[Theme]:
        """Get the currently applied theme."""
        return self._current_theme

    def apply_theme(self, theme_identifier: str, save_preference: bool = True) -> bool:
        """
        Apply a theme to the application.

        Args:
            theme_identifier: Theme ID from available themes
            save_preference: Whether to save this choice to config

        Returns:
            True if theme was applied successfully
        """
        logger.debug(f"Applying theme: {theme_identifier}")

        try:
            theme = self._available_themes.get(theme_identifier)
            if not theme:
                logger.error(f"Theme not found: {theme_identifier}")
                return False

            return self._apply_theme_internal(theme, save_preference)

        except Exception as e:
            logger.error(f"Error applying theme {theme_identifier}: {e}")
            return False

    def _apply_theme_internal(self, theme: Theme, save_preference: bool = True) -> bool:
        """Apply a theme configuration."""
        try:
            logger.debug(f"Applying theme: {theme}")

            # Load QSS content for the theme
            qss_content = self._load_theme_qss(theme)

            # Apply the QSS to the application
            self._app.setStyleSheet(qss_content)

            self._current_theme = theme

            # Save preference if requested
            if save_preference and self._config_service:
                self._config_service.set_theme_preference(theme.theme_id)

            # Emit signal
            self.theme_changed.emit(theme.theme_id)

            logger.info(f"Successfully applied theme: {theme.display_name}")
            return True

        except Exception as e:
            logger.error(f"Error applying theme {theme}: {e}")
            return False

    def apply_user_preference(self) -> bool:
        """
        Apply theme based on user preference from config.

        Returns:
            True if theme was applied successfully
        """
        if not self._config_service:
            logger.warning("No config service available, applying auto theme")
            return self.apply_theme("auto", False)

        try:
            preferred_theme = self._config_service.get_theme_preference()
            if preferred_theme and preferred_theme in self._available_themes:
                return self.apply_theme(preferred_theme, False)  # Don't re-save
            else:
                logger.debug("No valid theme preference found, applying auto theme")
                return self.apply_theme("auto", True)  # Save the auto preference

        except Exception as e:
            logger.error(f"Error applying user preference: {e}")
            return self.apply_theme("auto", True)

    def refresh_system_theme(self) -> bool:
        """
        Refresh system theme detection and re-apply auto theme if currently using it.

        Returns:
            True if refresh was successful
        """
        self._clear_system_theme_cache()

        # If current preference is auto, re-apply it
        if (
            self._config_service
            and self._config_service.get_theme_preference() == "auto"
        ):
            return self.apply_theme("auto", False)

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
                "theme_id": self._current_theme.theme_id,
                "display_name": self._current_theme.display_name,
                "category": self._current_theme.category.value,
                "theme_directory": self._current_theme.theme_directory,
                "description": self._current_theme.description,
                "version": self._current_theme.version,
                "qss_order": self._current_theme.qss_order,
            }

        return {
            "current_theme": current_theme_info,
            "available_themes": len(self._available_themes),
            "theme_list": [
                {
                    "id": theme.theme_id,
                    "name": theme.display_name,
                    "category": theme.category.value,
                    "directory": theme.theme_directory,
                    "description": theme.description,
                    "version": theme.version,
                    "qss_files": len(self._discover_qss_files(theme))
                    if theme.theme_directory
                    else 0,
                }
                for theme in self._available_themes.values()
            ],
            "system_theme": self._detect_system_theme().value,
            "user_preference": (
                self._config_service.get_theme_preference()
                if self._config_service
                else None
            ),
            "categories": [cat.value for cat in self.get_theme_categories()],
            "themes_root": str(self._dev_themes_root),
            "live_reload_enabled": self._enable_live_reload,
            "watched_files": len(self._watched_files) if self._watched_files else 0,
            "platform_info": self._get_platform_info(),
        }
