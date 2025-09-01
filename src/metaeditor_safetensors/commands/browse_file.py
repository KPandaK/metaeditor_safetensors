import os
import logging
from tkinter import filedialog, messagebox

from .command_base import Command

logger = logging.getLogger(__name__)

class BrowseFileCommand(Command):
    
    def execute(self):
        """Browse for a safetensors file."""
        self.result = None
        
        filepath = filedialog.askopenfilename(
            filetypes=[("Safetensors Files", "*.safetensors")],
            title="Select a safetensors file"
        )
        
        if filepath:
            # Validate file exists and is readable
            if not os.access(filepath, os.R_OK):
                messagebox.showerror("Error", f"File is not readable: {filepath}")
                return False
            
            # Log file selection and store result
            file_size_mb = os.path.getsize(filepath) / (1024**2)
            logger.info(f"Selected file: {filepath} ({file_size_mb:.1f} MB)")
            
            self.result = filepath
            return True
        else:
            logger.info("No file selected during browse operation")
            return False
    
    def can_execute(self):
        return True
    
    def get_description(self):
        return "Browse for and select a safetensors file to edit"
