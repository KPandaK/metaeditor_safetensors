import tkinter as tk
from tkinter import ttk
from .window_base import BaseWindow

class RawViewWindow(BaseWindow):
    
    def __init__(self, parent):
        super().__init__(parent)
        self.tree = None
    
    def _on_window_opened(self, metadata=None):
        if metadata is not None:
            self.update_metadata(metadata)
    
    def _on_window_closed(self):
        self.tree = None
    
    def update_metadata(self, metadata):
        if not self.is_open() or not self.tree:
            return
        
        # Clear existing content
        self.tree.delete(*self.tree.get_children())
        
        # Track key lengths for column sizing
        key_lengths = []
        
        def insert_items(parent, data):
            for key, value in sorted(data.items()):
                key_lengths.append(len(str(key)))
                if isinstance(value, dict):
                    # Create a parent node for nested dictionaries
                    node = self.tree.insert(parent, "end", text=key, values=("",))
                    insert_items(node, value)
                else:
                    # Insert leaf node with value
                    self.tree.insert(parent, "end", text=key, values=(str(value),))
        
        # Populate the tree
        insert_items("", metadata)
        
        # Auto-size the key column based on content
        if key_lengths:
            max_key_len = max(key_lengths)
            # Set width with reasonable min/max bounds
            key_width = max(100, min(20 + max_key_len * 7, 400))
            self.tree.column("#0", width=key_width, stretch=False)
        else:
            self.tree.column("#0", width=100, stretch=False)
        
        # Value column stretches to fill remaining space
        self.tree.column("value", width=200, stretch=True)
    
    def _create_window(self, *args, **kwargs):
        # Position window next to the main window
        main_x = self.parent.winfo_x()
        main_y = self.parent.winfo_y()
        main_width = self.parent.winfo_width()
        
        window_x = main_x + main_width + 10
        window_y = main_y
        
        # Create the window
        self.window = tk.Toplevel(self.parent)
        self.window.title("Raw Metadata")
        self.window.geometry(f"800x400+{window_x}+{window_y}")
        self.window.resizable(True, True)
        
        # Handle window close
        self._setup_window_close_handler()
        
        # Create the treeview
        self.tree = ttk.Treeview(self.window, columns=("value",), show="tree headings")
        self.tree.heading("#0", text="Key")
        self.tree.heading("value", text="Value")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
