import os
from importlib import resources
from pathlib import Path
from typing import Optional, Union


def get_project_root(start_path: Optional[Path] = None) -> Path:
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()

    # Search upward for project markers
    markers = ["pyproject.toml", ".git", "justfile"]
    for path in [start_path] + list(start_path.parents):
        for marker in markers:
            if (path / marker).exists():
                return path

    # Fallback to current directory if no markers found
    return start_path


def get_package_root(package_name: str = "metaeditor_safetensors") -> Path:
    try:
        package_files = resources.files(package_name)
        return Path(str(package_files))

    except Exception:
        # Fallback: find in project structure
        project_root = get_project_root()
        return project_root / package_name
