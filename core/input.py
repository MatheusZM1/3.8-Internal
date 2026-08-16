"""
REFERENCE: Tkinter keysym strings for is_pressed():
Letters/Numbers: 'a', '1'
Arrows: 'Left', 'Right', 'Up', 'Down'
Commands: 'Shift_L', 'Shift_R', 'Control_L', 'Alt_L'
Actions: 'Return', 'space', 'Tab', 'Escape', 'BackSpace'
F-Keys: 'F1' through 'F12'
"""

class InputManager:
    """This class keeps track of what keyboard keys are currently pressed."""
    def __init__(self, parent):
        """Initialise input manager."""
        self.parent = parent
    
        self.pressed_keys = set()
        
        # Bind the key press events
        parent.bind_all("<KeyPress>", self.on_press)
        parent.bind_all("<KeyRelease>", self.on_release)

    def on_press(self, event):
        """A key was pressed."""
        self.pressed_keys.add(event.keysym)

    def on_release(self, event):
        """A key was released."""
        # Discard avoids raising an error if the discarded item isn't present
        self.pressed_keys.discard(event.keysym)

    def is_pressed(self, key_name):
        """Check for a key press."""
        return key_name in self.pressed_keys