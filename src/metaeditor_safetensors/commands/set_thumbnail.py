import base64
import io
import logging
import os
from tkinter import filedialog, messagebox
from PIL import Image

from .command_base import Command
from config import THUMBNAIL_SIZE_WARNING, THUMBNAIL_TARGET_SIZE, THUMBNAIL_QUALITY

logger = logging.getLogger(__name__)

class SetThumbnailCommand(Command):
    
    def execute(self):
        self.result = None
        
        filepath = self._browse_for_image()
        if filepath:
            return self._process_image_file(filepath)
        return False
    
    def can_execute(self):
        return True
    
    def get_description(self):
        return "Set a thumbnail image for the model"

    def _browse_for_image(self):
        return filedialog.askopenfilename(
            filetypes=[
                ("Image Files", "*.jpg;*.jpeg;*.png;*.webp"), 
                ("JPEG Image", "*.jpg;*.jpeg"), 
                ("PNG Image", "*.png"), 
                ("WebP Image", "*.webp")
            ],
            title="Select a thumbnail image"
        )
    
    def _process_image_file(self, filepath):
        try:
            self.update_status("Processing image...")
            
            # Process image - call resize decision directly
            result = self._process_image(
                filepath, 
                target_size=THUMBNAIL_TARGET_SIZE,
                quality=THUMBNAIL_QUALITY,
                size_warning_threshold=THUMBNAIL_SIZE_WARNING
            )
            
            if result['success']:
                self.result = result['data_uri']
                self.clear_status()
                logger.info(f"Thumbnail set from: {filepath}")
                return True
            else:
                self.clear_status()
                logger.error(f"Error setting thumbnail: {result['error']}")
                messagebox.showerror("Error", f"Could not set thumbnail: {result['error']}")
                return False
                
        except Exception as e:
            self._handle_error(str(e))
            return False
    
    def _resize_image(self, img, target_size):
        original_width, original_height = img.size
        
        if original_width > original_height:
            new_width = target_size
            new_height = int((original_height * target_size) / original_width)
        else:
            new_height = target_size
            new_width = int((original_width * target_size) / original_height)
        
        return img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    
    def _process_image(self, filepath, target_size, quality, size_warning_threshold):
        try:
            file_size = os.path.getsize(filepath)
            
            with Image.open(filepath) as img:
                original_format = img.format
                
                # Check if file is too large and needs resizing
                should_resize = False
                if file_size > size_warning_threshold:
                    should_resize = messagebox.askyesno(
                        "Large Image File", 
                        f"Image file is {file_size / (1024 * 1024):.1f}MB. "
                        "Would you like to automatically resize it to reduce file size? "
                        f"(Will resize to fit within {THUMBNAIL_TARGET_SIZE}x{THUMBNAIL_TARGET_SIZE} while maintaining aspect ratio)"
                    )
                
                if should_resize:
                    # Resize the image while maintaining format
                    img_copy = self._resize_image(img, target_size)
                    
                    # Save in original format
                    img_bytes = io.BytesIO()
                    if original_format == 'JPEG':
                        img_copy.save(img_bytes, format='JPEG', quality=quality, optimize=True)
                        mime_type = 'image/jpeg'
                    elif original_format == 'PNG':
                        img_copy.save(img_bytes, format='PNG', optimize=True)
                        mime_type = 'image/png'
                    elif original_format == 'WEBP':
                        img_copy.save(img_bytes, format='WEBP', quality=quality, optimize=True)
                        mime_type = 'image/webp'
                    else:
                        # Fallback to JPEG for unknown formats
                        if img_copy.mode != 'RGB':
                            img_copy = img_copy.convert('RGB')
                        img_copy.save(img_bytes, format='JPEG', quality=quality, optimize=True)
                        mime_type = 'image/jpeg'
                    
                    img_bytes.seek(0)
                    b64 = base64.b64encode(img_bytes.read()).decode("utf-8")
                else:
                    # Use original file as-is
                    with open(filepath, 'rb') as f:
                        original_data = f.read()
                    b64 = base64.b64encode(original_data).decode("utf-8")
                    
                    if original_format == 'JPEG':
                        mime_type = 'image/jpeg'
                    elif original_format == 'PNG':
                        mime_type = 'image/png'
                    elif original_format == 'WEBP':
                        mime_type = 'image/webp'
                    else:
                        mime_type = 'image/jpeg'  # fallback
                
                data_uri = f"data:{mime_type};base64,{b64}"
                return {'success': True, 'data_uri': data_uri}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
