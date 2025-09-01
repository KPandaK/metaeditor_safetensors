import os
import shutil
import threading
import logging
import json
from tkinter import messagebox

from .command_base import Command
from utils import compute_sha256
from config import CHUNK_SIZE

logger = logging.getLogger(__name__)

class SaveCommand(Command):
    
    def __init__(self, editor, filepath, metadata, completion_callback=None):
        super().__init__(editor)
        self.filepath = filepath
        self.metadata = metadata
        self.completion_callback = completion_callback
    
    def execute(self):
        self.result = None
        
        if not self.filepath:
            messagebox.showerror("Error", "Please select a file first.")
            return False

        # Get user choice for backup
        choice = self._get_save_choice()

        # Start save operation in background thread
        save_thread = threading.Thread(
            target=self._save_threaded,
            args=(self.filepath, choice, self.metadata.copy()),
            daemon=True
        )
        save_thread.start()
        return True
    
    def _get_save_choice(self):
        return messagebox.askquestion(
            "Save Options",
            "Do you want to overwrite the existing file?\n\n"
            "Click 'Yes' to overwrite.\n"
            "Click 'No' to create a backup and then overwrite.",
            icon="question"
        )
    
    def _save_threaded(self, filepath, choice, metadata):
        try:
            # Compute hash if needed
            if "modelspec.hash_sha256" not in metadata:
                self.update_status_threadsafe("Computing file hash...")
                metadata["modelspec.hash_sha256"] = compute_sha256(filepath)

            tmp_path = filepath + ".tmp"
            backup_path = filepath + ".bak"

            # Always create backup first - safety first!
            self.update_status_threadsafe("Creating backup...")
            if os.path.exists(backup_path):
                os.remove(backup_path)
            shutil.copy2(filepath, backup_path)

            self._update_safetensors_metadata(
                filepath, 
                metadata, 
                tmp_path
            )

            # Replace original file with updated version
            self.update_status_threadsafe("Finalizing save...")
            os.remove(filepath)
            os.rename(tmp_path, filepath)

            # Remove backup only if user chose to overwrite and save succeeded
            if choice == "yes":
                os.remove(backup_path)
            
            # Success - notify completion
            if self.completion_callback:
                self.editor.after(0, lambda: self.completion_callback(True, filepath))
                
        except Exception as e:
            # Error - notify completion
            if self.completion_callback:
                self.editor.after(0, lambda: self.completion_callback(False, e))
    
    def _update_safetensors_metadata(self, filepath, new_metadata, tmp_path):
        def update_progress(message):
            self.update_status_threadsafe(message)
            logger.info(message)
        
        update_progress("Reading file header...")
        
        # Read the original file header to understand its structure
        with open(filepath, 'rb') as f:
            # Read header length (first 8 bytes)
            header_len_bytes = f.read(8)
            if len(header_len_bytes) != 8:
                raise ValueError("Invalid safetensors file: header length missing")
                
            header_len = int.from_bytes(header_len_bytes, byteorder='little')
            
            # Read the JSON header
            header_bytes = f.read(header_len)
            if len(header_bytes) != header_len:
                raise ValueError("Invalid safetensors file: header truncated")
                
            header_json = json.loads(header_bytes.decode('utf-8'))
            
            # The rest is tensor data - we'll copy this unchanged
            tensor_data_start = f.tell()
            file_size = os.path.getsize(filepath)
        
        # Update the metadata in the header
        if '__metadata__' not in header_json:
            header_json['__metadata__'] = {}
        
        # Merge our new metadata
        header_json['__metadata__'].update(new_metadata)
        
        # Create the new header
        new_header_str = json.dumps(header_json, separators=(',', ':'))
        new_header_bytes = new_header_str.encode('utf-8')
        new_header_len = len(new_header_bytes)
        
        update_progress("Creating file...")
        
        # Create new file with updated header and original tensor data
        with open(filepath, 'rb') as src, open(tmp_path, 'wb') as dst:
            # Write new header length
            dst.write(new_header_len.to_bytes(8, byteorder='little'))
            
            # Write new header
            dst.write(new_header_bytes)
            
            # Copy tensor data in chunks
            src.seek(tensor_data_start)
            
            update_progress("Copying tensor data...")
            
            chunk_size = CHUNK_SIZE
            copied = 0
            file_size_remaining = file_size - tensor_data_start
            last_progress_reported = -1
            
            while True:
                chunk = src.read(chunk_size)
                if not chunk:
                    break
                
                dst.write(chunk)
                copied += len(chunk)
                
                # Show progress every 2% for detailed feedback
                if file_size_remaining > 0:
                    progress = (copied / file_size_remaining) * 100
                    progress_int = int(progress / 2) * 2  # Round to nearest 2%
                    
                    if progress_int != last_progress_reported and progress_int % 2 == 0 and progress_int > 0:
                        update_progress(f"Copying tensor data: {progress_int}%")
                        last_progress_reported = progress_int
        
        update_progress("File update complete")
        logger.info("Metadata updated using optimized method")
    
    def can_execute(self):
        return self.filepath is not None
    
    def get_description(self):
        return f"Saves metadata to target file"
