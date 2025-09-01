"""
Command pattern implementation for SafetensorsEditor operations.

This module provides a clean separation between UI and business logic,
making the codebase more maintainable and testable.
"""

import os
import shutil
import threading
import logging
from abc import ABC, abstractmethod
from tkinter import filedialog, messagebox
from utils import compute_sha256, process_image
from metadata import update_safetensors_metadata
from config import (
    LARGE_FILE_WARNING_SIZE, THUMBNAIL_SIZE_WARNING,
    THUMBNAIL_TARGET_SIZE, THUMBNAIL_QUALITY
)

logger = logging.getLogger(__name__)

class Command(ABC):
    """Base command interface."""
    
    @abstractmethod
    def execute(self):
        """Execute the command."""
        pass

class BrowseFileCommand(Command):
    """Command to browse and select a safetensors file."""
    
    def __init__(self, editor):
        self.editor = editor
    
    def execute(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Safetensors Files", "*.safetensors")],
            title="Select a safetensors file"
        )
        if filepath:
            # Validate file exists and is readable
            if not os.access(filepath, os.R_OK):
                messagebox.showerror("Error", f"File is not readable: {filepath}")
                return
            
            # Check file size (warn for very large files)
            file_size = os.path.getsize(filepath)
            file_size_mb = file_size / (1024**2)
            file_size_gb = file_size / (1024**3)
            
            if file_size > LARGE_FILE_WARNING_SIZE:
                if file_size_gb > 1:
                    size_str = f"{file_size_gb:.1f} GB"
                else:
                    size_str = f"{file_size_mb:.0f} MB"
                    
                choice = messagebox.askyesno(
                    "Large File Warning", 
                    f"File is very large ({size_str}).\n"
                    f"Loading may take a while and use significant memory.\n\n"
                    f"Estimated memory usage: ~{file_size_mb * 2:.0f} MB\n"
                    f"Continue?"
                )
                if not choice:
                    return
            
            logger.info(f"Loading file: {filepath} ({file_size_mb:.1f} MB)")
            self.editor.update_status(f"Loading file ({file_size_mb:.1f} MB)...")
            self.editor.filepath_var.set(filepath)
            
            # Execute load metadata command
            LoadMetadataCommand(self.editor, filepath).execute()
        else:
            # Only disable buttons if no file is loaded
            if not self.editor.filepath_var.get():
                self.editor.set_button_states(showraw="disabled", set_img="disabled", view_img="disabled")


class LoadMetadataCommand(Command):
    """Command to load metadata from a safetensors file."""
    
    def __init__(self, editor, filepath):
        self.editor = editor
        self.filepath = filepath
    
    def execute(self):
        try:
            from safetensors import safe_open
            
            self.editor.update_status("Reading file metadata...")
            
            # Try to open and read metadata
            with safe_open(self.filepath, framework="pt") as f:
                model_metadata = f.metadata().copy() or {}
            
            self.editor.update_status("Updating interface...")
            
            # Success - update UI
            self.editor.metadata = model_metadata
            self.editor.populate_fields(model_metadata)
            self.editor.set_button_states(showraw="normal", set_img="normal")
            self.editor.update_view_img_state()
            if self.editor.sidecar and self.editor.sidecar.winfo_exists():
                self.editor.populate_sidecar_tree(model_metadata)
            
            self.editor.clear_status()
            logger.info(f"Loaded metadata from: {self.filepath}")
            
        except Exception as e:
            # Single catch-all with logging
            self.editor.clear_status()
            logger.error(f"Error loading {self.filepath}: {e}")
            messagebox.showerror("Error", f"Error reading file:\n{e}")
            self.editor._reset_ui_state()


class SaveChangesCommand(Command):
    """Command to save changes to the safetensors file."""
    
    def __init__(self, editor):
        self.editor = editor
    
    def execute(self):
        filepath = self.editor.filepath_var.get()
        if not filepath:
            messagebox.showerror("Error", "Please select a file first.")
            return

        # Validate inputs first
        is_valid, errors = self.editor.validate_inputs()
        if not is_valid:
            error_msg = "Please fix the following issues:\n\n" + "\n".join(f"• {error}" for error in errors)
            messagebox.showerror("Validation Error", error_msg)
            return

        choice = messagebox.askquestion(
            "Save Options",
            "Do you want to overwrite the existing file?\n\n"
            "Click 'Yes' to overwrite.\n"
            "Click 'No' to create a backup and then overwrite.",
            icon="question"
        )

        # Collect and update metadata
        metadata_updates = self.editor.collect_metadata_from_fields()
        self.editor.metadata.update(metadata_updates)

        # Start save operation in background thread
        save_thread = threading.Thread(
            target=self._save_threaded,
            args=(filepath, choice, self.editor.metadata.copy()),
            daemon=True
        )
        save_thread.start()
    
    def _save_threaded(self, filepath, choice, metadata):
        """Background thread for save operations."""
        try:
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
            
            # Success - update UI on main thread
            self.editor.after(0, lambda: self._save_success(filepath))
            
        except Exception as e:
            # Error - update UI on main thread  
            self.editor.after(0, lambda: self._save_error(e))
    
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


class SetThumbnailCommand(Command):
    """Command to set thumbnail image."""
    
    def __init__(self, editor):
        self.editor = editor
    
    def execute(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.jpg;*.jpeg;*.png;*.webp"), ("JPEG Image", "*.jpg;*.jpeg"), ("PNG Image", "*.png"), ("WebP Image", "*.webp")],
            title="Select a thumbnail image"
        )
        if filepath:
            try:
                # Close any open image viewer since we're setting a new image
                if self.editor.image_viewer and self.editor.image_viewer.winfo_exists():
                    self.editor._close_image_viewer()
                    
                self.editor.update_status("Processing image...")
                
                # Process image with callback for resize decision
                def ask_resize(file_size_mb):
                    return messagebox.askyesno(
                        "Large Image File", 
                        f"Image file is {file_size_mb:.1f}MB. "
                        "Would you like to automatically resize it to reduce file size? "
                        f"(Will resize to fit within {THUMBNAIL_TARGET_SIZE}x{THUMBNAIL_TARGET_SIZE} while maintaining aspect ratio)"
                    )
                
                result = process_image(
                    filepath, 
                    target_size=THUMBNAIL_TARGET_SIZE,
                    quality=THUMBNAIL_QUALITY,
                    size_warning_threshold=THUMBNAIL_SIZE_WARNING,
                    resize_callback=ask_resize
                )
                
                if result['success']:
                    self.editor.thumbnail_var.set(result['data_uri'])
                    self.editor.update_view_img_state()
                    self.editor.clear_status()
                    logger.info(f"Thumbnail set from: {filepath}")
                else:
                    self.editor.clear_status()
                    raise Exception(result['error'])
                    
            except Exception as e:
                self.editor.clear_status()
                logger.error(f"Error setting thumbnail: {e}")
                messagebox.showerror("Error", f"Could not set thumbnail: {e}")


class ViewThumbnailCommand(Command):
    """Command to view thumbnail image."""
    
    def __init__(self, editor):
        self.editor = editor
    
    def execute(self):
        # Check if image viewer is already open - if so, close it
        if self.editor.image_viewer and self.editor.image_viewer.winfo_exists():
            self.editor._close_image_viewer()
            return
            
        data_uri = self.editor.thumbnail_var.get()
        if not data_uri.startswith("data:image/jpeg;base64,"):
            messagebox.showerror("Error", "No valid thumbnail image set.")
            return
        
        try:
            import base64
            import io
            from PIL import Image, ImageTk
            import tkinter as tk
            
            b64 = data_uri.split(",", 1)[1]
            img_data = base64.b64decode(b64)
            image = Image.open(io.BytesIO(img_data))
            
            # Create new image viewer window
            self.editor.image_viewer = tk.Toplevel(self.editor)
            self.editor.image_viewer.title("Thumbnail Preview")
            self.editor.image_viewer.resizable(False, False)
            
            # Position the image viewer to the left of the main window
            main_x = self.editor.winfo_x()
            main_y = self.editor.winfo_y()
            main_width = self.editor.winfo_width()
            main_height = self.editor.winfo_height()
            
            img_width = image.width
            img_height = image.height
            
            # Position to the left of main window with some spacing
            left_x = main_x - img_width - 10  # 10px gap
            # Center vertically relative to main window
            center_y = main_y + (main_height - img_height) // 2
            
            # Ensure window doesn't go off-screen to the left
            if left_x < 0:
                left_x = 10  # Minimum distance from screen edge
            
            self.editor.image_viewer.geometry(f"{img_width}x{img_height}+{left_x}+{center_y}")
            
            # Clean up reference when window is closed
            self.editor.image_viewer.protocol("WM_DELETE_WINDOW", self.editor._close_image_viewer)
            
            img_tk = ImageTk.PhotoImage(image)
            lbl = tk.Label(self.editor.image_viewer, image=img_tk)
            lbl.image = img_tk  # Keep a reference to prevent garbage collection
            lbl.pack()
            
            # Update button text to "Close Image"
            self.editor.view_img_btn.config(text="Close Image (Ctrl+V)")
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not display image: {e}")


class ToggleRawViewCommand(Command):
    """Command to toggle raw metadata view."""
    
    def __init__(self, editor):
        self.editor = editor
    
    def execute(self):
        if self.editor.sidecar and self.editor.sidecar.winfo_exists():
            self.editor.close_sidecar()
            self.editor.showraw_btn.config(text="Show Raw (F12)")
        else:
            self.editor.open_sidecar()
            self.editor.showraw_btn.config(text="Hide Raw (F12)")


class ShowAboutCommand(Command):
    """Command to show about dialog."""
    
    def __init__(self, editor):
        self.editor = editor
    
    def execute(self):
        self.editor.show_about()
