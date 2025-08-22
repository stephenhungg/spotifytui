"""
Main Spotify TUI application
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Static, Label
from textual.widgets import DataTable, Input, Select, ProgressBar
from textual.screen import Screen, ModalScreen
from textual.reactive import reactive
from textual import work
from textual import events
import asyncio
import logging

from .spotify_client import SpotifyClient
from .screens import (
    PlayerScreen,
    PlaylistsScreen,
    SearchScreen,
    ArtistScreen,
    AlbumScreen,
    LyricsScreen
)

logger = logging.getLogger(__name__)

class SpotifyTUI(App):
    """Main Spotify TUI application."""
    
    # CSS_PATH = "styles.css"  # Commented out to use default styling
    TITLE = "Spotify TUI 🎵"
    SUB_TITLE = "Control Spotify from your terminal"
    
    def __init__(self):
        super().__init__()
        self.spotify_client = None
        self.current_screen = "player"
        self.focus_index = 0
        self.focusable_widgets = []
    
    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header()
        
        with Container(id="main-container"):
            with Horizontal(id="sidebar"):
                yield Button("🎵 Player", id="btn-player", variant="primary")
                yield Button("📚 Playlists", id="btn-playlists")
                yield Button("🔍 Search", id="btn-search")
                yield Button("👤 Artists", id="btn-artists")
                yield Button("💿 Albums", id="btn-albums")
                yield Button("📝 Lyrics", id="btn-lyrics")
            
            with Container(id="content-area"):
                yield PlayerScreen(id="player-screen")
                yield PlaylistsScreen(id="playlists-screen", classes="hidden")
                yield SearchScreen(id="search-screen", classes="hidden")
                yield ArtistScreen(id="artist-screen", classes="hidden")
                yield AlbumScreen(id="album-screen", classes="hidden")
                yield LyricsScreen(id="lyrics-screen", classes="hidden")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Initialize the application when mounted."""
        print("App mounted, initializing...")  # Debug
        self.initialize_spotify()
        self.show_screen("player")
        self.update_focusable_widgets()
        self.focus_first_widget()
        
        # Update footer with keyboard help
        footer = self.query_one("Footer")
        if footer:
            footer.text = "← → Navigate Screens | 1-6 Number Keys | Space: Play/Pause | Esc: Exit"
        
        print("App initialization complete")  # Debug
    
    def update_focusable_widgets(self):
        """Update the list of focusable widgets for navigation."""
        self.focusable_widgets = []
        
        # Add sidebar buttons
        for i in range(6):  # 6 sidebar buttons
            btn = self.query_one(f"#btn-{'player' if i == 0 else 'playlists' if i == 1 else 'search' if i == 2 else 'artists' if i == 3 else 'albums' if i == 4 else 'lyrics'}")
            if btn:
                self.focusable_widgets.append(btn)
        
        # Add content area widgets based on current screen
        if self.current_screen == "player":
            # Player controls
            for widget_id in ["btn-previous", "btn-play-pause", "btn-next", "btn-stop", "btn-volume-up", "btn-volume-down"]:
                widget = self.query_one(f"#{widget_id}")
                if widget:
                    self.focusable_widgets.append(widget)
        
        elif self.current_screen == "search":
            # Search controls
            for widget_id in ["search-input", "search-type", "btn-search"]:
                widget = self.query_one(f"#{widget_id}")
                if widget:
                    self.focusable_widgets.append(widget)
        
        elif self.current_screen == "playlists":
            # Playlist controls
            for widget_id in ["btn-refresh-playlists", "btn-new-playlist"]:
                widget = self.query_one(f"#{widget_id}")
                if widget:
                    self.focusable_widgets.append(widget)
    
    def focus_first_widget(self):
        """Focus the first focusable widget."""
        if self.focusable_widgets:
            self.focus_index = 0
            self.focusable_widgets[0].focus()
    
    def focus_next_widget(self):
        """Focus the next widget in the navigation order."""
        if self.focusable_widgets:
            self.focus_index = (self.focus_index + 1) % len(self.focusable_widgets)
            self.focusable_widgets[self.focus_index].focus()
    
    def focus_previous_widget(self):
        """Focus the previous widget in the navigation order."""
        if self.focusable_widgets:
            self.focus_index = (self.focus_index - 1) % len(self.focusable_widgets)
            self.focusable_widgets[self.focus_index].focus()
    
    def on_key(self, event: events.Key) -> None:
        """Handle keyboard navigation."""
        if event.key == "left":
            # Navigate to previous screen
            screens = ["player", "playlists", "search", "artists", "albums", "lyrics"]
            current_index = screens.index(self.current_screen)
            prev_index = (current_index - 1) % len(screens)
            self.show_screen(screens[prev_index])
            event.prevent_default()
        elif event.key == "right":
            # Navigate to next screen
            screens = ["player", "playlists", "search", "artists", "albums", "lyrics"]
            current_index = screens.index(self.current_screen)
            next_index = (current_index + 1) % len(screens)
            self.show_screen(screens[next_index])
            event.prevent_default()
        elif event.key == "space":
            # Toggle play/pause when on player screen
            if self.current_screen == "player":
                play_btn = self.query_one("#btn-play-pause")
                if play_btn:
                    play_btn.press()
            event.prevent_default()
        elif event.key == "escape":
            # Exit the application
            self.exit()
            event.prevent_default()
        elif event.key in ["1", "2", "3", "4", "5", "6"]:
            # Number keys to switch screens directly
            screens = ["player", "playlists", "search", "artists", "albums", "lyrics"]
            index = int(event.key) - 1
            if 0 <= index < len(screens):
                self.show_screen(screens[index])
            event.prevent_default()
    
    @work
    async def initialize_spotify(self):
        """Initialize Spotify client asynchronously."""
        try:
            self.spotify_client = SpotifyClient()
            self.notify("✅ Connected to Spotify", severity="information")
        except Exception as e:
            self.notify(f"❌ Failed to connect to Spotify: {e}", severity="error")
            logger.error(f"Spotify initialization failed: {e}")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button press events."""
        button_id = event.button.id
        print(f"Button pressed: {button_id}")  # Debug logging
        
        if button_id == "btn-player":
            self.show_screen("player")
        elif button_id == "btn-playlists":
            self.show_screen("playlists")
        elif button_id == "btn-search":
            self.show_screen("search")
        elif button_id == "btn-artists":
            self.show_screen("artists")
        elif button_id == "btn-albums":
            self.show_screen("albums")
        elif button_id == "btn-lyrics":
            self.show_screen("lyrics")
    
    def show_screen(self, screen_name: str):
        """Show a specific screen and hide others."""
        screens = {
            "player": "player-screen",
            "playlists": "playlists-screen",
            "search": "search-screen",
            "artists": "artist-screen",
            "albums": "album-screen",
            "lyrics": "lyrics-screen"
        }
        
        # Hide all screens
        for screen_id in screens.values():
            screen = self.query_one(f"#{screen_id}")
            screen.add_class("hidden")
        
        # Show selected screen
        if screen_name in screens:
            screen = self.query_one(f"#{screens[screen_name]}")
            screen.remove_class("hidden")
            self.current_screen = screen_name
            
            # Update button states
            for btn_id, screen_id in screens.items():
                btn = self.query_one(f"#btn-{btn_id}")
                if btn_id == screen_name:
                    btn.add_class("active")
                else:
                    btn.remove_class("active")
            
            # Update focusable widgets for new screen
            self.update_focusable_widgets()
            # Don't reset focus - let it stay on the currently focused widget
    
    def get_spotify_client(self) -> SpotifyClient:
        """Get the Spotify client instance."""
        return self.spotify_client
