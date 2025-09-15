from enum import Enum
from typing import List

from pydantic import BaseModel, Field


class WindowSettings(BaseModel):
    width: int = 1100
    height: int = 800


class Settings(BaseModel):
    config_version: str = "1.0"
    recent_files: List[str] = []
    theme: str = "system"
    window: WindowSettings = Field(default_factory=WindowSettings)
