import logging
from tkinter import messagebox

from .command_base import Command
from safetensors import read_safetensors_metadata

logger = logging.getLogger(__name__)

class LoadMetadataCommand(Command):
    
    def __init__(self, editor, filepath):
        super().__init__(editor)
        self.filepath = filepath
    
    def execute(self):
        self.result = None
        
        try:
            self._load_metadata()
            return True
        except Exception as e:
            self._handle_error(e)
            return False
    
    def _load_metadata(self):
        self.update_status("Reading file metadata...")

        # Use our custom safetensors reader - only get metadata
        model_metadata = read_safetensors_metadata(self.filepath)
        
        # Store result for editor to use
        self.result = model_metadata
        
        logger.info(f"Loaded metadata from: {self.filepath}")
    
    def _handle_error(self, error):
        self.editor.clear_status()
        logger.error(f"Error loading {self.filepath}: {error}")
        messagebox.showerror("Error", f"Error reading file:\n{error}")
    
    def can_execute(self):
        return self.filepath and self.editor
    
    def get_description(self):
        return f"Load metadata from target file"
