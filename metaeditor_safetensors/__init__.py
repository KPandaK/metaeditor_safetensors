def main():
    """Entry point for the application."""
    from .app import main as app_main

    return app_main()


__all__ = ["main"]
