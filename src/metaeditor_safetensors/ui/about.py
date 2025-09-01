import tkinter as tk
import tkinter.font as tkfont
import webbrowser
from config import GITHUB_URL
from _version import __version__
from .window_base import BaseWindow

class AboutWindow(BaseWindow):
    
    def __init__(self, parent, keyboard_manager=None):
        super().__init__(parent)
        self.keyboard_manager = keyboard_manager
    
    def _create_window(self):
        # Create new about window
        self.window = tk.Toplevel(self.parent)
        self.window.title("About MetaEditor Safetensors")
        self.window.resizable(False, False)
        
        # Create all content first (without positioning the window)
        self._create_content()
        
        # Update the window to calculate its natural size
        self.window.update_idletasks()
        
        # Now center the window based on its actual size
        self._center_window()
        
        # Handle window close
        self._setup_window_close_handler()
    
    def _create_content(self):
        """Create all the window content."""
        # Use the same font as the main application
        default_font = tkfont.nametofont("TkDefaultFont")
        title_font = default_font.copy()
        title_font.configure(size=default_font["size"] + 3, weight="bold")
        small_font = default_font.copy()
        small_font.configure(size=default_font["size"] - 1)
        link_font = default_font.copy()
        link_font.configure(underline=True)
        
        # Main content
        tk.Label(self.window, text="MetaEditor Safetensors", font=title_font).pack(pady=(12,2))
        tk.Label(self.window, text=f"Version {__version__}", font=default_font).pack()
        tk.Label(self.window, text="Author: KPandaK", font=default_font).pack(pady=(2,8))
        
        # Keyboard shortcuts section
        shortcuts_frame = tk.LabelFrame(self.window, text="Keyboard Shortcuts", font=default_font)
        shortcuts_frame.pack(padx=20, pady=(0,10), fill="x")
        
        # Get shortcuts content
        shortcuts_content = self._get_shortcuts_content()
        num_lines = shortcuts_content.count('\n') + 1
        
        # Create text widget with dynamic height using monospace font for alignment
        shortcuts_text = tk.Text(shortcuts_frame, height=num_lines, width=45, font=("Consolas", 10), wrap="none")
        shortcuts_text.pack(padx=5, pady=5)
        shortcuts_text.insert("1.0", shortcuts_content)
        shortcuts_text.config(state="disabled")
        
        def open_github(event=None):
            webbrowser.open_new(GITHUB_URL)

        link = tk.Label(self.window, text="GitHub Repository", fg="blue", cursor="hand2", font=link_font)
        link.pack()
        link.bind("<Button-1>", open_github)

        tk.Button(self.window, text="Close", command=self.close, font=default_font).pack(pady=10)
    
    def _get_shortcuts_content(self):
        if self.keyboard_manager:
            shortcuts_list = self.keyboard_manager.get_shortcuts_list()
            return "\n".join([f"{key:<10} {desc}" for key, desc in shortcuts_list])
    
    def _center_window(self):
        # Get parent window position and size
        main_x = self.parent.winfo_x()
        main_y = self.parent.winfo_y()
        main_width = self.parent.winfo_width()
        main_height = self.parent.winfo_height()
        
        # Get the actual size of the about window
        about_width = self.window.winfo_reqwidth()
        about_height = self.window.winfo_reqheight()
        
        # Calculate center position
        center_x = main_x + (main_width - about_width) // 2
        center_y = main_y + (main_height - about_height) // 2
        
        # Set the window position (without specifying size, let it use natural size)
        self.window.geometry(f"+{center_x}+{center_y}")
