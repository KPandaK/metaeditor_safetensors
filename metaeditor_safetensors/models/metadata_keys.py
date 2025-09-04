"""
Metadata Keys
=============

This module centralizes the metadata keys used throughout the application.
Using these constants helps prevent typos and makes refactoring easier.
"""

class MetadataKeys:
    """
    A container for metadata key strings.
    
    The keys follow the 'modelspec' standard for safetensors metadata.
    """
    # --- Main Fields ---
    TITLE = "modelspec.title"
    DESCRIPTION = "modelspec.description"
    AUTHOR = "modelspec.author"
    DATE = "modelspec.date"
    LICENSE = "modelspec.license"
    USAGE_HINT = "modelspec.usage_hint"
    
    # --- Complex Fields ---
    TAGS = "modelspec.tags"
    MERGED_FROM = "modelspec.merged_from"
    
    # --- Thumbnail ---
    THUMBNAIL = "modelspec.thumbnail"
