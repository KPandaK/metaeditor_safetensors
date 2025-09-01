from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

@dataclass
class Shortcut:
    """Represents a keyboard shortcut."""
    key_combination: str
    action: Callable
    description: str
    enabled_check: Optional[Callable] = None

class KeyboardManager:
    
    def __init__(self, widget):
        """Initialize with a tkinter widget to bind shortcuts to."""
        self.widget = widget
        self.shortcuts: Dict[str, Shortcut] = {}
        self._setup_default_shortcuts()
    
    def _setup_default_shortcuts(self):
        """Set up the default keyboard shortcuts."""
        # This will be populated by the editor when it passes its methods
        pass
    
    def add_shortcut(self, key_combination: str, action: Callable, 
                    description: str, enabled_check: Optional[Callable] = None):
        """Add a keyboard shortcut."""
        shortcut = Shortcut(key_combination, action, description, enabled_check)
        self.shortcuts[key_combination] = shortcut
        
        # Create the binding with optional enabled check
        def handle_shortcut(event):
            if enabled_check is None or enabled_check():
                action()
        
        self.widget.bind_all(key_combination, handle_shortcut)
    
    def remove_shortcut(self, key_combination: str):
        """Remove a keyboard shortcut."""
        if key_combination in self.shortcuts:
            self.widget.unbind_all(key_combination)
            del self.shortcuts[key_combination]
    
    def get_shortcuts_list(self) -> List[tuple]:
        """Get a list of all shortcuts for display purposes."""
        shortcuts_list = []
        for key, shortcut in self.shortcuts.items():
            # Convert key combination to display format
            display_key = self._format_key_for_display(key)
            shortcuts_list.append((display_key, shortcut.description))
        return sorted(shortcuts_list)
    
    def _format_key_for_display(self, key_combination: str) -> str:
        """Format key combination for user-friendly display."""
        # Convert tkinter key format to user-friendly format
        key = key_combination.replace('<', '').replace('>', '')
        key = key.replace('Control-', 'Ctrl+')
        key = key.replace('-', '+')
        return key