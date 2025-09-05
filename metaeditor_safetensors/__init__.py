"""
Safetensors Metadata Editor Package
==================================

A simple, intuitive tool for viewing and editing metadata in Safetensors model files.
"""

def main():
    """Entry point for the application."""
    from .app import main as app_main
    return app_main()

__all__ = ['main']