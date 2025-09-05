import base64
import io
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from .window_base import BaseWindow
from .window_positioning import WindowPositioner, HorizontalAlignment, VerticalAlignment

class ImageViewerWindow(BaseWindow):
    
    def open(self, data_uri):
        try:
            self.original_image = self._decode_image(data_uri)
            self.current_image = self.original_image
            super().open()  # Call base class open which will call _create_window
            return True
        except Exception as e:
            messagebox.showerror("Error", f"Could not display image: {e}")
            return False
    
    def _decode_image(self, data_uri):
        b64 = data_uri.split(",", 1)[1]
        img_data = base64.b64decode(b64)
        return Image.open(io.BytesIO(img_data))
    
    def _create_window(self):
        # Create new viewer window
        self.window = tk.Toplevel(self.parent)
        self.window.title("Thumbnail Preview")
        self.window.resizable(True, True)
        
        # Get screen dimensions
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Calculate max window size (80% of screen, leaving room for taskbar/borders)
        max_width = int(screen_width * 0.8)
        max_height = int(screen_height * 0.8)
        
        # Calculate initial window size based on image
        img_width = self.original_image.width
        img_height = self.original_image.height
        
        # Scale down if image is larger than max dimensions
        if img_width > max_width or img_height > max_height:
            # Calculate scaling factor to fit within max dimensions
            scale_x = max_width / img_width
            scale_y = max_height / img_height
            scale = min(scale_x, scale_y)
            
            window_width = int(img_width * scale)
            window_height = int(img_height * scale)
        else:
            window_width = img_width
            window_height = img_height
        
        # Set minimum size (reasonable minimum for usability)
        min_size = 200
        window_width = max(window_width, min_size)
        window_height = max(window_height, min_size)
        
        # Position the window using smart positioning utility
        WindowPositioner.position_window(self.window, self.parent, window_width, window_height, 
                HorizontalAlignment.LEFT, VerticalAlignment.TOP_EDGE)
        self.window.minsize(min_size, min_size)
        
        self._setup_window_close_handler()
        self.window.bind('<Configure>', self._on_window_resize)
        
        # Create and display the image
        self._create_image_display()
        self._update_displayed_image()
    
    def _create_image_display(self):
        # Create a frame to hold the image label
        self.image_frame = tk.Frame(self.window)
        self.image_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create label for the image
        self.image_label = tk.Label(self.image_frame)
        self.image_label.pack(expand=True)
    
    def _update_displayed_image(self):
        # Get current window size (minus some padding for borders)
        self.window.update_idletasks()
        window_width = self.image_frame.winfo_width()
        window_height = self.image_frame.winfo_height()
        
        if window_width <= 1 or window_height <= 1:
            # Window not fully initialized yet
            self.window.after(10, self._update_displayed_image)
            return
        
        # Calculate scaling to fit image in window while maintaining aspect ratio
        img_width = self.original_image.width
        img_height = self.original_image.height
        
        scale_x = window_width / img_width
        scale_y = window_height / img_height
        scale = min(scale_x, scale_y)
        
        # Don't upscale beyond original size
        scale = min(scale, 1.0)
        
        new_width = max(1, int(img_width * scale))
        new_height = max(1, int(img_height * scale))
        
        # Resize image if needed
        if new_width != img_width or new_height != img_height:
            self.current_image = self.original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            self.current_image = self.original_image
        
        # Update the display
        img_tk = ImageTk.PhotoImage(self.current_image)
        self.image_label.configure(image=img_tk)
        self.image_label.image = img_tk  # Keep reference to prevent garbage collection
    
    def _on_window_resize(self, event):
        # Only respond to resize events for the main window, not child widgets
        if event.widget == self.window:
            # Delay the update slightly to avoid excessive updates during resizing
            if hasattr(self, '_resize_after_id'):
                self.window.after_cancel(self._resize_after_id)
            self._resize_after_id = self.window.after(50, self._update_displayed_image)
