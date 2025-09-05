import tkinter as tk
from enum import Enum

class HorizontalAlignment(Enum):
    """Horizontal alignment options"""
    LEFT = "left"           # Position to the left of parent
    RIGHT = "right"         # Position to the right of parent
    CENTER = "center"       # Center horizontally on parent
    LEFT_EDGE = "left_edge" # Align with left edge of parent
    RIGHT_EDGE = "right_edge" # Align with right edge of parent

class VerticalAlignment(Enum):
    """Vertical alignment options"""
    TOP = "top"             # Position above parent
    BOTTOM = "bottom"       # Position below parent
    CENTER = "center"       # Center vertically on parent
    TOP_EDGE = "top_edge"   # Align with top edge of parent
    BOTTOM_EDGE = "bottom_edge" # Align with bottom edge of parent

class WindowPositioner:
    """Utility class for positioning windows relative to other windows"""
    
    @staticmethod
    def position_window(window, parent, width=None, height=None, 
                       h_align=HorizontalAlignment.LEFT, 
                       v_align=VerticalAlignment.CENTER,
                       gap=10):
        # Update both windows to get current geometry
        parent.update_idletasks()
        window.update_idletasks()
        
        # Get window dimensions - use provided values or auto-detect
        if width is None:
            width = window.winfo_reqwidth()
            if width <= 1:  # Fallback if reqwidth isn't reliable
                width = window.winfo_width()
        
        if height is None:
            height = window.winfo_reqheight()
            if height <= 1:  # Fallback if reqheight isn't reliable
                height = window.winfo_height()
        
        # Get parent window properties
        parent_x = parent.winfo_x()
        parent_y = parent.winfo_y()
        parent_width = parent.winfo_width()
        parent_height = parent.winfo_height()
        
        # Get screen dimensions
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        # Calculate horizontal position
        x = WindowPositioner._calculate_x_position(
            parent_x, parent_width, width, h_align, gap, screen_width
        )
        
        # Calculate vertical position
        y = WindowPositioner._calculate_y_position(
            parent_y, parent_height, height, v_align, gap, screen_height
        )

        # Always ensure window fits on screen with buffer
        x, y = WindowPositioner._fit_on_screen_with_buffer(
            x, y, width, height, screen_width, screen_height, buffer=20
        )
        
        # Set window geometry
        window.geometry(f"{width}x{height}+{x}+{y}")
        
        return x, y
    
    @staticmethod
    def _calculate_x_position(parent_x, parent_width, width, h_align, gap, screen_width):
        """Calculate horizontal position based on alignment"""
        if h_align == HorizontalAlignment.LEFT:
            return parent_x - width - gap
        elif h_align == HorizontalAlignment.RIGHT:
            return parent_x + parent_width + gap
        elif h_align == HorizontalAlignment.CENTER:
            return parent_x + (parent_width - width) // 2
        elif h_align == HorizontalAlignment.LEFT_EDGE:
            return parent_x
        elif h_align == HorizontalAlignment.RIGHT_EDGE:
            return parent_x + parent_width - width
        else:
            return parent_x  # Default fallback
    
    @staticmethod
    def _calculate_y_position(parent_y, parent_height, height, v_align, gap, screen_height):
        """Calculate vertical position based on alignment"""
        if v_align == VerticalAlignment.TOP:
            return parent_y - height - gap
        elif v_align == VerticalAlignment.BOTTOM:
            return parent_y + parent_height + gap
        elif v_align == VerticalAlignment.CENTER:
            return parent_y + (parent_height - height) // 2
        elif v_align == VerticalAlignment.TOP_EDGE:
            return parent_y
        elif v_align == VerticalAlignment.BOTTOM_EDGE:
            return parent_y + parent_height - height
        else:
            return parent_y  # Default fallback
    
    @staticmethod
    def _fit_on_screen_with_buffer(x, y, width, height, screen_width, screen_height, buffer=20):
        """
        Adjust coordinates to ensure window fits on screen with buffer space.
        
        Args:
            x: Current x coordinate
            y: Current y coordinate
            width: Window width
            height: Window height
            screen_width: Screen width
            screen_height: Screen height
            buffer: Minimum buffer space from screen edges (pixels)
            
        Returns:
            tuple: (adjusted_x, adjusted_y) coordinates
        """
        # Adjust X coordinate
        if x < buffer:
            # Window is too far left, move it to minimum position
            x = buffer
        elif x + width > screen_width - buffer:
            # Window extends too far right, move it left
            x = screen_width - buffer - width
        
        # Adjust Y coordinate
        if y < buffer:
            # Window is too far up, move it to minimum position
            y = buffer
        elif y + height > screen_height - buffer:
            # Window extends too far down, move it up
            y = screen_height - buffer - height
        
        return x, y
