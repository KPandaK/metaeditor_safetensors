"""
Command to save changes to the safetensors file.
"""

import os
import shutil
import threading
import logging
from tkinter import messagebox

from .command_base import Command
from utils import compute_sha256
from metadata import update_safetensors_metadata

logger = logging.getLogger(__name__)


class SaveChangesCommand(Command):
    """Command to save changes to the safetensors file."""
    
    def execute(self):
        """Save changes to the safetensors file."""
        filepath = self.editor.filepath_var.get()
        if not filepath:
            messagebox.showerror("Error", "Please select a file first.")
            return

        # Validate inputs first
        if not self._validate_inputs():
            return

        # Get user choice for backup
        choice = self._get_save_choice()

        # Collect and update metadata
        metadata_updates = self.editor.collect_metadata_from_fields()
        self.editor.metadata.update(metadata_updates)

        # Start save operation in background thread
        self._start_save_thread(filepath, choice, self.editor.metadata.copy())
    
    def _validate_inputs(self):
        """Validate user inputs before saving."""
        is_valid, errors = self.editor.validate_inputs()
        if not is_valid:
            error_msg = "Please fix the following issues:\n\n" + "\n".join(f"• {error}" for error in errors)
            messagebox.showerror("Validation Error", error_msg)
            return False
        return True
    
    def _get_save_choice(self):
        """Get user choice for save options."""
        return messagebox.askquestion(
            "Save Options",
            "Do you want to overwrite the existing file?\n\n"
            "Click 'Yes' to overwrite.\n"
            "Click 'No' to create a backup and then overwrite.",
            icon="question"
        )
    
    def _start_save_thread(self, filepath, choice, metadata):
        """Start the save operation in a background thread."""
        save_thread = threading.Thread(
            target=self._save_threaded,
            args=(filepath, choice, metadata),
            daemon=True
        )
        save_thread.start()
    
    def _save_threaded(self, filepath, choice, metadata):
        """Background thread for save operations."""
        try:
            self._perform_save(filepath, choice, metadata)
            # Success - update UI on main thread
            self.editor.after(0, lambda: self._save_success(filepath))
        except Exception as e:
            # Error - update UI on main thread  
            self.editor.after(0, lambda: self._save_error(e))
    
    def _perform_save(self, filepath, choice, metadata):
        """Perform the actual save operation."""
        # Compute hash if needed
        if "modelspec.hash_sha256" not in metadata:
            self.editor.update_status_threadsafe("Computing file hash...")
            metadata["modelspec.hash_sha256"] = compute_sha256(filepath)

        tmp_path = filepath + ".tmp"
        backup_path = filepath + ".bak"

        # Always create backup first - safety first!
        self.editor.update_status_threadsafe("Creating backup...")
        if os.path.exists(backup_path):
            os.remove(backup_path)
        shutil.copy2(filepath, backup_path)

        # Use the optimized safetensors metadata update
        method_used = update_safetensors_metadata(
            filepath, 
            metadata, 
            tmp_path, 
            progress_callback=self.editor.update_status_threadsafe
        )
        
        if method_used == "optimized":
            logger.info("Metadata updated using optimized method")
        else:
            logger.info("Metadata updated using standard method")

        # Replace original file with updated version
        self.editor.update_status_threadsafe("Finalizing save...")
        os.remove(filepath)
        os.rename(tmp_path, filepath)
        
        # If user doesn't want backup, clean it up
        if choice == "yes":
            os.remove(backup_path)
    
    def _save_success(self, filepath):
        """Called on main thread when save succeeds."""
        self.editor.clear_status()
        logger.info(f"File saved: {filepath}")
        messagebox.showinfo("Complete", f"File saved to:\n{filepath}")

    def _save_error(self, error):
        """Called on main thread when save fails."""
        self.editor.clear_status()
        logger.error(f"Error saving file: {error}")
        messagebox.showerror("Error", f"Error saving file:\n{error}")
    
    def can_execute(self):
        """Check if the save command can be executed."""
        return self.editor.filepath_var.get() is not None
    
    def get_description(self):
        """Get command description."""
        return "Save changes to the safetensors file"
