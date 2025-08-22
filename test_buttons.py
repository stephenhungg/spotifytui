#!/usr/bin/env python3
"""
Simple test to check if Textual buttons work
"""

from textual.app import App, ComposeResult
from textual.widgets import Button, Header, Footer

class ButtonTestApp(App):
    """Simple app to test button functionality."""
    
    def compose(self) -> ComposeResult:
        yield Header()
        yield Button("Test Button 1", id="btn1")
        yield Button("Test Button 2", id="btn2")
        yield Footer()
    
    def on_button_pressed(self, event):
        print(f"Button pressed: {event.button.id}")
        self.notify(f"Button {event.button.id} was pressed!")
    
    def on_button_clicked(self, event):
        print(f"Button clicked: {event.button.id}")
        self.notify(f"Button {event.button.id} was clicked!")

if __name__ == "__main__":
    app = ButtonTestApp()
    app.run()




