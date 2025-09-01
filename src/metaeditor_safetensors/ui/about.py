import tkinter as tk
import webbrowser
from config import GITHUB_URL
from _version import __version__
from base_window import BaseWindow

class AboutWindow(BaseWindow):
    
    def _create_window(self):
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
        shortcuts_text.insert("1.0", 
            "Ctrl+O     Open file\n"
            "Ctrl+S     Save changes\n"
            "Ctrl+I     Set thumbnail image\n"
            "Ctrl+V     View thumbnail image\n"
            "F12        Toggle raw metadata view\n"
            "F1         Show this help\n"
            "Esc        Exit application"
        )
        shortcuts_text.config(state="disabled")
        
        def open_github(event=None):
            webbrowser.open_new(GITHUB_URL)

        link = tk.Label(self.window, text="GitHub Repository", fg="blue", cursor="hand2", font=("TkDefaultFont", 10, "underline"))
        link.pack()
        link.bind("<Button-1>", open_github)

        tk.Button(self.window, text="Close", command=self.close).pack(pady=10)
        
        # Handle window close
        self._setup_window_close_handler()
