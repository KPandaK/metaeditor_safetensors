import tkinter as tk

class BaseWindow:
    """Base class for all UI windows with common open/close functionality."""
    
    def __init__(self, parent):
        self.parent = parent
        self.window = None
    
    def open(self, *args, **kwargs):
        """Open the window. Override _create_window() in subclasses."""
        if self.is_open():
            # Window already exists, just bring it to front
            self.window.lift()
            self.window.focus()
            self._on_window_opened(*args, **kwargs)
            return
        
        # Create new window
        self._create_window(*args, **kwargs)
        self._on_window_opened(*args, **kwargs)
    
    def close(self):
        """Close the window."""
        if self.window is not None:
            self._on_window_closing()
            self.window.destroy()
            self.window = None
            self._on_window_closed()
    
    def is_open(self):
        """Check if the window is currently open."""
        return self.window is not None and self.window.winfo_exists()
    
    # Backward compatibility aliases
    def show(self, *args, **kwargs):
        """Show the window (alias for open)."""
        self.open(*args, **kwargs)
    
    def hide(self):
        """Hide the window (alias for close)."""
        self.close()
    
    # Template methods for subclasses to override
    def _create_window(self, *args, **kwargs):
        """Create the window. Must be implemented by subclasses."""
        raise NotImplementedError("Subclasses must implement _create_window()")
    
    def _on_window_opened(self, *args, **kwargs):
        """Called after window is opened (new or existing). Override if needed."""
        pass
    
    def _on_window_closing(self):
        """Called just before window is closed. Override if needed."""
        pass
    
    def _on_window_closed(self):
        """Called after window is closed. Override if needed."""
        pass

    def _setup_window_close_handler(self):
        """Set up the window close handler. Call this in _create_window()."""
        if self.window:
            self.window.protocol("WM_DELETE_WINDOW", self.close)
