"""
Theme Model
===========

Theme data model with self-loading capabilities for QSS stylesheets.
"""

import glob
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)


class Theme:
    """Represents a modular QSS theme configuration with self-loading capabilities."""

    def __init__(
        self,
        theme_id: str,
        name: str,
        category: str,
        theme_directory: Optional[Path] = None,
        description: Optional[str] = None,
        version: str = "1.0.0",
        qss_order: Optional[List[str]] = None,
        settings: Optional[Dict[str, Any]] = None,
    ):
        self.theme_id = theme_id
        self.name = name
        self.description = description or f"Theme: {name}"
        self.category = category
        self.version = version
        self.theme_directory = theme_directory
        self.settings = settings or {}
        self.qss_order = qss_order or []

        # Cache for combined QSS content
        self._qss_cache: Optional[str] = None

    @classmethod
    def from_directory(cls, theme_directory: Path) -> "Theme":
        # Find the yaml file in the directory
        yaml_files = list(theme_directory.glob("*.yaml"))
        if not yaml_files:
            raise ValueError(
                f"No YAML file found in theme directory: {theme_directory}"
            )

        # Try to load YAML configuration
        config = cls._load_theme_config(yaml_files[0])

        # Extract config values with defaults
        theme_id = config.get("theme_id", theme_directory.stem)
        name = config.get("name", "Unknown Theme")
        description = config.get("description")
        version = config.get("version", "1.0.0")
        category = config.get("category", theme_id).lower()
        qss_order = config.get("qss_order", [])
        settings = config.get("settings", {})

        # Handle QSS file discovery and ordering
        if qss_order:
            # Use specified order from YAML
            final_qss_order = qss_order[:]

            # Find any additional QSS files not listed in the order
            all_qss_files = {f.name for f in theme_directory.glob("*.qss")}
            specified_files = set(qss_order)
            unspecified_files = all_qss_files - specified_files

            # Append any unspecified files alphabetically
            if unspecified_files:
                final_qss_order.extend(sorted(unspecified_files))
        else:
            # No order specified - discover all QSS files alphabetically
            qss_files = sorted(theme_directory.glob("*.qss"))
            final_qss_order = [f.name for f in qss_files]

        return cls(
            theme_id=theme_id,
            name=name,
            description=description,
            category=category,
            version=version,
            theme_directory=theme_directory,
            settings=settings,
            qss_order=final_qss_order,
        )

    @staticmethod
    def _load_theme_config(yaml_file: Path) -> Dict[str, Any]:
        """
        Load YAML configuration from a file.

        Returns:
            dict: Parsed YAML configuration as a dictionary.
            If the YAML file is invalid or empty, returns an empty dictionary.

        Raises:
            ValueError: If the YAML file contains invalid YAML syntax.
        """
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)

                # Handle empty file (returns None)
                if config is None:
                    logger.debug(f"Empty YAML file, using defaults: {yaml_file}")
                    return {}

                # Ensure we got a dictionary
                if isinstance(config, dict):
                    logger.debug(f"Loaded theme config: {yaml_file}")
                    return config
                else:
                    logger.warning(f"YAML file is not a dictionary: {yaml_file}")
                    return {}

        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML syntax in {yaml_file}: {e}")
        except Exception as e:
            raise ValueError(f"Error reading theme config from {yaml_file}: {e}")

    @staticmethod
    def _infer_category(theme_id: str) -> str:
        """Infer theme category from theme ID."""
        theme_lower = theme_id.lower()
        if any(word in theme_lower for word in ["light", "bright", "white"]):
            return "light"
        elif any(word in theme_lower for word in ["dark", "night", "black"]):
            return "dark"
        else:
            return "dark"  # Default to dark

    def get_qss(self) -> str:
        """
        Get combined QSS content for this theme.

        Returns:
            Combined QSS stylesheet as string
        """
        # Return cached content if available
        if self._qss_cache is not None:
            return self._qss_cache

        if not self.theme_directory:
            return ""

        combined_qss = []

        for filename in self.qss_order:
            qss_file = self.theme_directory / filename

            if qss_file.exists():
                try:
                    with open(qss_file, "r", encoding="utf-8") as f:
                        content = f.read().strip()
                        if content:
                            # Only add file origin comment if there are multiple QSS files
                            if len(self.qss_order) > 1:
                                combined_qss.append(
                                    f"/* From: {filename} */\n{content}"
                                )
                            else:
                                combined_qss.append(content)
                            logger.debug(f"Loaded QSS: {qss_file}")
                except Exception as e:
                    logger.error(f"Error loading QSS file {qss_file}: {e}")
            else:
                logger.warning(f"QSS file not found: {qss_file}")

        # Combine and cache
        self._qss_cache = "\n\n".join(combined_qss)
        if len(self.qss_order) == 1:
            logger.debug(
                f"Loaded single QSS file with {len(self._qss_cache):,} characters"
            )
        else:
            logger.debug(
                f"Combined {len(self.qss_order)} QSS files into {len(self._qss_cache):,} characters"
            )

        return self._qss_cache

    def clear_cache(self):
        """Clear cached QSS content (useful for live reloading)."""
        self._qss_cache = None

    def get_qss_file_paths(self) -> List[Path]:
        """Get list of QSS file paths for this theme (useful for file watching)."""
        if not self.theme_directory:
            return []

        return [self.theme_directory / filename for filename in self.qss_order]

    def __str__(self):
        return f"{self.name} ({self.theme_id})"

    def __repr__(self):
        return f"Theme('{self.theme_id}', '{self.name}', '{self.category}')"
