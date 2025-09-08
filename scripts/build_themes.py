import logging
from pathlib import Path

import yaml

from metaeditor_safetensors.services.file_service import (
    get_package_root,
    get_project_root,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def scan_themes_directory(themes_root: Path) -> dict:
    """Scan the themes directory and build a registry of available themes."""
    registry = {"version": "1.0.0", "generated_by": "build_themes.py", "themes": {}}

    if not themes_root.exists():
        logger.warning(f"Themes directory not found: {themes_root}")
        return registry

    for theme_dir in themes_root.iterdir():
        if not theme_dir.is_dir():
            continue

        yaml_files = list(theme_dir.glob("*.yaml")) + list(theme_dir.glob("*.yml"))
        if not yaml_files:
            logger.warning(f"No YAML config file found for theme: {theme_dir.name}")
            continue

        config_file = yaml_files[0]

        try:
            with open(config_file, "r", encoding="utf-8") as f:
                theme_config = yaml.safe_load(f)

            theme_info = {
                "theme_id": theme_dir.name,
                "config_file": config_file.name,
                "name": theme_config.get("name", theme_dir.name.title()),
                "description": theme_config.get("description", ""),
                "category": theme_config.get("category", "custom"),
                "version": theme_config.get("version", "1.0.0"),
                "qss_files": [],
            }

            qss_files = list(theme_dir.glob("*.qss"))
            theme_info["qss_files"] = [qss_file.name for qss_file in qss_files]

            registry["themes"][theme_dir.name] = theme_info
            logger.info(
                f"Added theme to registry: {theme_dir.name} ({theme_info['name']})"
            )

        except Exception as e:
            logger.error(f"Error processing theme {theme_dir.name}: {e}")
            continue

    return registry


def write_registry(registry: dict, output_path: Path):
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            yaml.dump(registry, f, default_flow_style=False, indent=2, sort_keys=False)
        logger.info(f"Theme registry written to: {output_path}")
        logger.info(
            f"Processed {len(registry['themes'])} themes: {list(registry['themes'].keys())}"
        )
    except Exception as e:
        logger.error(f"Error writing registry to {output_path}: {e}")
        raise


def main():
    project_root = get_project_root()
    package_dir = get_package_root()

    themes_root = project_root / "assets" / "themes"
    output_path = package_dir / "themes_registry.yaml"

    logger.info("Building theme registry...")
    logger.info(f"Scanning themes in: {themes_root}")
    logger.info(f"Output registry to: {output_path}")

    registry = scan_themes_directory(themes_root)

    write_registry(registry, output_path)

    logger.info("Theme registry build complete!")


if __name__ == "__main__":
    main()
