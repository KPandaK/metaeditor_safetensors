import base64
import io
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
from base_window import BaseWindow

class ImageViewerWindow(BaseWindow):
    
    def open(self, data_uri):
        try:
            self.image = self._decode_image(data_uri)
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
        self.window.resizable(False, False)
        
        # Position the window
        self._position_window(self.image)
        
        # Handle window close
        self._setup_window_close_handler()
        
        # Display the image
        self._display_image(self.image)
    
    def _position_window(self, image):
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_height = self.parent.winfo_height()
        
        img_width = image.width
        img_height = image.height
        
        # Position to the left of parent window with some spacing
        left_x = parent_x - img_width - 10  # 10px gap
        # Center vertically relative to parent window
        center_y = parent_y + (parent_height - img_height) // 2
        
        # Ensure window doesn't go off-screen to the left
        if left_x < 0:
            left_x = 10  # Minimum distance from screen edge
        
        self.window.geometry(f"{img_width}x{img_height}+{left_x}+{center_y}")
    
    def _display_image(self, image):
        img_tk = ImageTk.PhotoImage(image)
        label = tk.Label(self.window, image=img_tk)
        label.image = img_tk  # Keep reference to prevent garbage collection
        label.pack()
