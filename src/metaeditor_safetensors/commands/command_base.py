from abc import ABC, abstractmethod

class Command(ABC):
    
    def __init__(self, editor):
        self.editor = editor
        self.result = None  # Store command execution results
    
    @abstractmethod
    def execute(self):
        pass

    def update_status(self, message):
        self.editor.update_status(message)

    def update_status_threadsafe(self, message):
        self.editor.after(0, lambda: self.editor.update_status(message))

    def clear_status(self):
        self.editor.clear_status()

    def can_execute(self):
        return True
    
    def get_description(self):
        return f"{self.__class__.__name__} command"
