import logging
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)


class ThemeType(str, Enum):
    """Theme categories for visual filtering and grouping."""

    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class ThemeConfig(BaseModel):
    theme_id: str
    name: str
    category: ThemeType = ThemeType.LIGHT
    description: Optional[str] = None
    version: str = "1.0.0"
    qss_order: List[str] = []


class Theme:
    def __init__(
        self,
        config: ThemeConfig,
        directory: Path,
        qss_order: List[str],
    ):
        self.config: ThemeConfig = config
        self.directory: Path = directory
        self.qss_order: List[str] = qss_order
        # Cache for combined QSS content
        self._qss_cache: Optional[str] = None

    @classmethod
    def from_directory(cls, directory: Path) -> "Theme":
        # Find the yaml file in the directory
        yaml_files = list(directory.glob("*.yaml"))
        if not yaml_files:
            raise ValueError(f"No YAML file found in theme directory: {directory}")

        # Try to load YAML configuration
        config = cls._load_theme_config(yaml_files[0])

        # Handle QSS file discovery and ordering
        if config.qss_order:
            # Use specified order from YAML
            final_qss_order = config.qss_order[:]

            # Find any additional QSS files not listed in the order
            all_qss_files = {f.name for f in directory.glob("*.qss")}
            specified_files = set(final_qss_order)
            unspecified_files = all_qss_files - specified_files

            # Append any unspecified files alphabetically
            if unspecified_files:
                final_qss_order.extend(sorted(unspecified_files))
        else:
            # No order specified - discover all QSS files alphabetically
            qss_files = sorted(directory.glob("*.qss"))
            final_qss_order = [f.name for f in qss_files]

        return cls(
            config=config,
            directory=directory,
            qss_order=final_qss_order,
        )

    @staticmethod
    def _load_theme_config(yaml_file: Path) -> ThemeConfig:
        try:
            with open(yaml_file, "r", encoding="utf-8") as f:
                yaml_data = yaml.safe_load(f)
            return ThemeConfig.model_validate(yaml_data)
        except Exception as e:
            raise ValueError(f"Error reading theme config from {yaml_file}: {e}")

    def get_qss(self) -> str:
        # Return cached content if available
        if self._qss_cache is not None:
            return self._qss_cache

        if not self.directory:
            return ""

        combined_qss = []

        for filename in self.qss_order:
            qss_file = self.directory / filename

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
        self._qss_cache = None

    def get_qss_file_paths(self) -> List[Path]:
        if not self.directory:
            return []

        return [self.directory / filename for filename in self.qss_order]
