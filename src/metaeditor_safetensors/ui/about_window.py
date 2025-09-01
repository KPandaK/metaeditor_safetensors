import tkinter as tk
import webbrowser
from config import GITHUB_URL
from _version import __version__

class AboutWindow:
    
    def __init__(self, parent, keyboard_manager=None):
        self.parent = parent
        self.keyboard_manager = keyboard_manager
        self.window = None
    
    def open(self):
        """Open the about window."""
        if self.is_open():
            # Window already exists, just bring it to front
            self.window.lift()
            self.window.focus()
            return
        
        self._create_window()
    
    def close(self):
        """Close the about window."""
        if self.window is not None:
            self.window.destroy()
            self.window = None
    
    def is_open(self):
        """Check if the about window is currently open."""
        return self.window is not None and self.window.winfo_exists()
    
    # Keep show() and hide() for backward compatibility
    def show(self):
        """Show the about window (alias for open)."""
        self.open()
    
    def hide(self):
        """Hide the about window (alias for close)."""
        self.close()
    
    def _create_window(self):
        """Create the about window."""
        # Create new about window
        self.window = tk.Toplevel(self.parent)
        self.window.title("About MetaEditor Safetensors")
        self.window.resizable(False, False)
        
        # Center the about window over the main window
        main_x = self.parent.winfo_x()
        main_y = self.parent.winfo_y()
        main_width = self.parent.winfo_width()
        main_height = self.parent.winfo_height()
        
        about_width = 400
        about_height = 350
        
        center_x = main_x + (main_width - about_width) // 2
        center_y = main_y + (main_height - about_height) // 2
        
        self.window.geometry(f"{about_width}x{about_height}+{center_x}+{center_y}")

        # Main content
        tk.Label(self.window, text="MetaEditor Safetensors", font=("TkDefaultFont", 12, "bold")).pack(pady=(12,2))
        tk.Label(self.window, text=f"Version {__version__}", font=("TkDefaultFont", 10)).pack()
        tk.Label(self.window, text="A simple tool for viewing and editing safetensors metadata.", wraplength=380, justify="center").pack(pady=(6,2))
        tk.Label(self.window, text="Author: KPandaK", font=("TkDefaultFont", 9)).pack(pady=(2,8))
        
        # Keyboard shortcuts section
        shortcuts_frame = tk.LabelFrame(self.window, text="Keyboard Shortcuts", font=("TkDefaultFont", 9))
        shortcuts_frame.pack(padx=20, pady=(0,10), fill="x")
        
        shortcuts_text = tk.Text(shortcuts_frame, height=6, width=45, font=("TkDefaultFont", 8), wrap="none")
        shortcuts_text.pack(padx=5, pady=5)
        
        # Get shortcuts from keyboard manager if available
        if self.keyboard_manager:
            shortcuts_display = []
            for shortcut in self.keyboard_manager.shortcuts:
                shortcuts_display.append(f"{shortcut.key_sequence:<10} {shortcut.description}")
            shortcuts_content = "\n".join(shortcuts_display)
        
        shortcuts_text.insert("1.0", shortcuts_content)
        shortcuts_text.config(state="disabled")
        
        def open_github(event=None):
            webbrowser.open_new(GITHUB_URL)

        link = tk.Label(self.window, text="GitHub Repository", fg="blue", cursor="hand2", font=("TkDefaultFont", 10, "underline"))
        link.pack()
        link.bind("<Button-1>", open_github)

        tk.Button(self.window, text="Close", command=self.close).pack(pady=10)
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.close)
