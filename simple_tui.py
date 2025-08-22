#!/usr/bin/env python3
"""
Simple working Spotify TUI
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Button, Static, Label, Input
from textual.reactive import reactive
from textual import work
import asyncio

from src.spotify_client import SpotifyClient
import requests
from PIL import Image
import io

class SimpleSpotifyTUI(App):
    """Simple working Spotify TUI."""
    
    TITLE = "Spotify TUI 🎵"
    CSS_PATH = "styles.css"
    
    current_track = reactive("Loading...")
    current_artist = reactive("")
    current_album = reactive("")
    is_playing = reactive(False)
    track_progress_ms = reactive(0)
    track_duration_ms = reactive(0)
    album_art_url = reactive("")
    current_album_art_ascii = ""
    current_screen = reactive("player")
    playlist_cursor = reactive(0)
    track_cursor = reactive(0)
    playlists_data = []
    current_playlist_tracks = []
    viewing_tracks = reactive(False)
    tracks_scroll_offset = reactive(0)
    
    def __init__(self):
        super().__init__()
        self.spotify_client = None
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container():
            # Main content with player and playlists side by side
            with Horizontal():
                # Left side - Player
                with Container(id="player-section", classes="player-panel"):
                    yield Static(id="player-content")
                
                # Right side - Playlists
                with Container(id="playlist-section", classes="playlist-panel"):
                    yield Static(id="playlist-content")
            

        
        yield Footer()
    
    def on_mount(self):
        """Initialize the app."""
        self.init_spotify()
        self.update_screen()
        self.set_interval(2, self.update_music)
        
        # Add help text to footer
        footer = self.query_one("Footer")
        footer.text = "🎮 j/k: Navigate | Enter: Select/Play | Space: Play/Pause | N/P: Skip | B/ESC: Back | Q: Quit"
    
    @work
    async def init_spotify(self):
        """Initialize Spotify client."""
        try:
            self.spotify_client = SpotifyClient()
            self.notify("✅ Connected to Spotify!")
        except Exception as e:
            self.notify(f"❌ Spotify error: {e}")
    
    @work
    async def update_music(self):
        """Update music info."""
        if not self.spotify_client:
            return
        
        try:
            playback = self.spotify_client.get_current_playback()
            if playback and playback.get('item'):
                track = playback['item']
                self.current_track = track.get('name', 'Unknown')
                self.current_artist = ', '.join([a['name'] for a in track.get('artists', [])])
                self.current_album = track.get('album', {}).get('name', 'Unknown')
                self.is_playing = playback.get('is_playing', False)
                self.track_progress_ms = playback.get('progress_ms', 0)
                self.track_duration_ms = track.get('duration_ms', 0)
                
                # Get album art URL and process it
                album = track.get('album', {})
                images = album.get('images', [])
                if images:
                    # Get the smallest image for faster loading
                    new_url = images[-1].get('url', '')
                    if new_url != self.album_art_url:
                        self.album_art_url = new_url
                        self.download_and_process_album_art()
                
                self.update_screen()
            else:
                self.current_track = "No music playing"
                self.current_artist = ""
                self.current_album = ""
                self.is_playing = False
                self.track_progress_ms = 0
                self.track_duration_ms = 0
                self.album_art_url = ""
                self.update_screen()
        except Exception as e:
            self.current_track = f"Error: {e}"
            self.update_screen()
    
    def update_screen(self):
        """Update both player and playlist panels."""
        # Update player panel
        player_content = self.query_one("#player-content")
        player_content.update(self.get_player_display())
        
        # Update playlist panel
        playlist_content = self.query_one("#playlist-content")
        if self.viewing_tracks:
            playlist_content.update(self.get_tracks_view())
        else:
            playlist_content.update(self.get_playlists_text())
    
    def get_player_display(self):
        """Create an epic player display with progress bar and ASCII art."""
        if self.current_track == "No music playing":
            return """
🎵 SPOTIFY TUI
   
╔══════════════════════════════════════╗
║                                      ║
║         No music playing             ║
║                                      ║
║     Start playing music in Spotify   ║
║        and it will appear here!      ║
║                                      ║
╚══════════════════════════════════════╝

Controls: Space - Play/Pause | N/→ - Next | P/← - Previous | 1-6 - Navigate | Q - Quit
"""
        
        # Status and playback info
        status_icon = "▶️" if self.is_playing else "⏸️"
        status_text = "PLAYING" if self.is_playing else "PAUSED"
        
        # Time formatting
        progress_sec = self.track_progress_ms // 1000
        duration_sec = self.track_duration_ms // 1000
        progress_time = f"{progress_sec // 60}:{progress_sec % 60:02d}"
        duration_time = f"{duration_sec // 60}:{duration_sec % 60:02d}"
        
        # Progress bar (40 characters wide)
        if self.track_duration_ms > 0:
            progress_ratio = self.track_progress_ms / self.track_duration_ms
            filled_chars = int(progress_ratio * 40)
            progress_bar = "█" * filled_chars + "░" * (40 - filled_chars)
        else:
            progress_bar = "░" * 40
            progress_ratio = 0
        
        # Album art (ASCII style)
        album_art = self.get_ascii_album_art()
        
        # Create the display
        text = f"""
🎵 SPOTIFY TUI - {status_text} {status_icon}

{album_art}

╔══════════════════════════════════════════════════════════════╗
║  🎵 {self.current_track[:50]}{'.' * (50 - len(self.current_track)) if len(self.current_track) < 50 else ''}  ║
║  👤 {self.current_artist[:50]}{'.' * (50 - len(self.current_artist)) if len(self.current_artist) < 50 else ''}  ║
║  💿 {self.current_album[:50]}{'.' * (50 - len(self.current_album)) if len(self.current_album) < 50 else ''}  ║
╠══════════════════════════════════════════════════════════════╣
║  {progress_time} [{progress_bar}] {duration_time}  ║
║  Progress: {progress_ratio * 100:.1f}%{'':>40}║
╚══════════════════════════════════════════════════════════════╝

Controls:
Space - Play/Pause | N/→ - Next Track | P/← - Previous Track | 1-6 - Navigate Screens | Q - Quit
"""
        return text
    
    @work
    async def download_and_process_album_art(self):
        """Download album art and convert to 16x16 pixel art."""
        if not self.album_art_url:
            return
        
        try:
            # Download the image
            response = requests.get(self.album_art_url, timeout=5)
            if response.status_code == 200:
                # Open image with PIL
                img = Image.open(io.BytesIO(response.content))
                
                # Convert to 32x32 pixels for better detail
                img_resized = img.resize((32, 32), Image.LANCZOS)
                
                # Convert to RGB if needed
                if img_resized.mode != 'RGB':
                    img_resized = img_resized.convert('RGB')
                
                # Create ASCII art from the 32x32 image
                self.current_album_art_ascii = self.image_to_clean_ascii(img_resized)
                self.update_screen()
        except Exception as e:
            print(f"Failed to process album art: {e}")
            self.current_album_art_ascii = self.get_default_album_art()
    
    def image_to_clean_ascii(self, img):
        """Convert 32x32 PIL image to clean black/white ASCII art."""
        # Clean ASCII characters for better gradients
        ascii_chars = [' ', '░', '▒', '▓', '█']
        
        # Get pixel data
        pixels = img.load()
        ascii_art = "    ╔════════════════════════════════════╗\n"
        
        for y in range(16):  # Use 16 rows for square proportions
            line = "    ║"
            for x in range(16):  # Use 16 columns
                # Sample from 32x32 image but display as 16x16
                sample_x = x * 2
                sample_y = y * 2
                r, g, b = pixels[sample_x, sample_y]
                
                # Calculate brightness using proper luminance formula
                brightness = int(0.299 * r + 0.587 * g + 0.114 * b)
                
                # Map brightness to ASCII character (0-255 -> 0-4)
                char_index = min(brightness * len(ascii_chars) // 256, len(ascii_chars) - 1)
                char = ascii_chars[char_index]
                
                # Double characters to make it more square (terminal chars are taller than wide)
                line += char + char
            line += "║\n"
            ascii_art += line
        
        ascii_art += "    ╚════════════════════════════════════╝"
        return ascii_art
    
    def image_to_colorful_ascii(self, img):
        """Convert 32x32 PIL image to colorful ASCII art."""
        # Get pixel data
        pixels = img.load()
        ascii_art = "    ╔════════════════════════════════════════════════════════════════╗\n"
        
        for y in range(32):
            line = "    ║"
            for x in range(32):
                r, g, b = pixels[x, y]
                
                # Calculate brightness
                brightness = (r + g + b) // 3
                
                # Add some color based on dominant RGB values
                if brightness < 30:
                    char = '⚫'  # Very dark
                elif brightness < 60:
                    char = '🟫'  # Dark brown
                elif brightness < 90:
                    if r > g and r > b:
                        char = '🟥'  # Dark red
                    elif g > r and g > b:
                        char = '🟩'  # Dark green  
                    elif b > r and b > g:
                        char = '🟦'  # Dark blue
                    else:
                        char = '⬛'  # Black
                elif brightness < 120:
                    if r > g + 30 and r > b + 30:
                        char = '🔴'  # Red
                    elif g > r + 30 and g > b + 30:
                        char = '🟢'  # Green
                    elif b > r + 30 and b > g + 30:
                        char = '🔵'  # Blue
                    else:
                        char = '⬜'  # Gray
                elif brightness < 150:
                    if r > g + 20 and r > b + 20:
                        char = '🟠'  # Orange
                    elif g > r + 20 and g > b + 20:
                        char = '🟡'  # Yellow
                    elif b > r + 20 and b > g + 20:
                        char = '🟣'  # Purple
                    else:
                        char = '⬜'  # Light gray
                else:
                    char = '⚪'  # White/bright
                
                line += char
            line += "║\n"
            ascii_art += line
        
        ascii_art += "    ╚════════════════════════════════════════════════════════════════╝"
        return ascii_art
    
    def image_to_ascii_blocks(self, img):
        """Convert PIL image to ASCII block art (fallback)."""
        # Color mapping for different brightness levels
        ascii_chars = [' ', '░', '▒', '▓', '█']
        
        # Get pixel data
        pixels = img.load()
        ascii_art = "    ╔════════════════════════════════════╗\n"
        
        for y in range(min(16, img.height)):
            line = "    ║"
            for x in range(min(16, img.width)):
                r, g, b = pixels[x, y]
                # Calculate brightness
                brightness = (r + g + b) // 3
                # Map brightness to ASCII character
                char_index = min(brightness // 51, len(ascii_chars) - 1)
                # Use double characters for better aspect ratio
                line += ascii_chars[char_index] * 2
            line += "║\n"
            ascii_art += line
        
        ascii_art += "    ╚════════════════════════════════════╝"
        return ascii_art
    
    def get_ascii_album_art(self):
        """Get the processed album art or default."""
        if self.current_album_art_ascii:
            return self.current_album_art_ascii
        else:
            return self.get_default_album_art()
    
    def get_default_album_art(self):
        """Default album art when no image is available."""
        return """
    ╔════════════════════════════════════╗
    ║ ♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪ ║
    ║ ♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪ ║
    ║ ♪♪♪♪♪♪♪♪♪♪♪♪🎵🎵♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪ ║
    ║ ♪♪♪♪♪♪♪♪♪♪♪♪🎵🎵♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪ ║
    ║ ♪♪♪♪♪♪♪♪♪♪♪♪🎵🎵♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪ ║
    ║ ♪♪♪♪♪♪♪♪♪♪♪♪🎵🎵♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪ ║
    ║ ♪♪♪♪♪♪♪♪♪♪♪♪🎵🎵♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪ ║
    ║ ♪♪♪♪♪♪♪♪♪♪♪♪🎵🎵♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪ ║
    ║ ♪♪♪♪♪♪♪♪♪♪♪♪🎵🎵♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪ ║
    ║ ♪♪♪♪♪♪♪♪♪♪♪♪🎵🎵♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪ ║
    ║ ♪♪♪♪♪♪♪♪♪♪♪♪🎵🎵♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪ ║
    ║ ♪♪♪♪♪♪♪♪♪♪♪♪🎵🎵♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪ ║
    ║ ♪♪♪♪♪♪♪♪♪♪♪♪🎵🎵♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪ ║
    ║ ♪♪♪♪♪♪♪♪♪♪♪♪🎵🎵♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪ ║
    ║ ♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪ ║
    ║ ♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪♪ ║
    ╚════════════════════════════════════╝
"""
    
    def get_playlists_text(self):
        """Get playlists or track view with VIM-style cursor."""
        if not self.spotify_client:
            return "📚 PLAYLISTS\n\n❌ Not connected to Spotify"
        
        if self.viewing_tracks:
            return self.get_tracks_view()
        else:
            return self.get_playlists_view()
    
    def get_playlists_view(self):
        """Show the main playlists view."""
        try:
            playlists = self.spotify_client.get_user_playlists()
            if not playlists:
                return "📚 PLAYLISTS\n\n🔍 No playlists found"
            
            # Store playlists data for later use
            self.playlists_data = playlists[:15]  # Show first 15
            
            # Reset cursor if out of bounds
            if self.playlist_cursor >= len(self.playlists_data):
                self.playlist_cursor = 0
            
            text = "📚 YOUR PLAYLISTS\n"
            text += "Use ↑↓/j/k to navigate, Enter to view tracks, P to play playlist\n\n"
            
            for i, playlist in enumerate(self.playlists_data):
                name = playlist.get('name', 'Unknown')
                tracks = playlist.get('tracks', {}).get('total', 0)
                owner = playlist.get('owner', {}).get('display_name', 'Unknown')
                
                # Add cursor indicator like Vim
                cursor = "►" if i == self.playlist_cursor else " "
                highlight = "[bold green]" if i == self.playlist_cursor else ""
                end_highlight = "[/bold green]" if i == self.playlist_cursor else ""
                
                text += f"{cursor} {highlight}{name}{end_highlight}\n"
                text += f"   👤 {owner} | 🎵 {tracks} tracks\n\n"
            
            if len(playlists) > 15:
                text += f"... and {len(playlists) - 15} more playlists"
            
            return text
        except Exception as e:
            return f"📚 PLAYLISTS\n\n❌ Error loading playlists: {e}"
    
    def get_tracks_view(self):
        """Show tracks in the selected playlist with scrolling."""
        if not self.current_playlist_tracks:
            return "🎵 LOADING TRACKS..."
        
        if not self.playlists_data or self.playlist_cursor >= len(self.playlists_data):
            return "❌ Error: Invalid playlist"
        
        playlist_name = self.playlists_data[self.playlist_cursor].get('name', 'Unknown')
        total_tracks = len(self.current_playlist_tracks)
        
        # Reset track cursor if out of bounds
        if self.track_cursor >= total_tracks:
            self.track_cursor = 0
        
        # Calculate scrolling window (show 15 tracks at a time)
        window_size = 15
        
        # Auto-scroll when cursor moves outside window
        if self.track_cursor < self.tracks_scroll_offset:
            self.tracks_scroll_offset = self.track_cursor
        elif self.track_cursor >= self.tracks_scroll_offset + window_size:
            self.tracks_scroll_offset = self.track_cursor - window_size + 1
        
        # Make sure scroll offset doesn't go negative or too far
        self.tracks_scroll_offset = max(0, min(self.tracks_scroll_offset, total_tracks - window_size))
        
        start_idx = self.tracks_scroll_offset
        end_idx = min(start_idx + window_size, total_tracks)
        
        text = f"🎵 TRACKS IN: {playlist_name}\n"
        text += f"Showing {start_idx + 1}-{end_idx} of {total_tracks} tracks | ↑↓/j/k navigate, Enter play, ESC/B back\n\n"
        
        for i in range(start_idx, end_idx):
            track_item = self.current_playlist_tracks[i]
            track = track_item.get('track', {})
            if not track:
                continue
                
            name = track.get('name', 'Unknown Track')
            artists = ', '.join([artist['name'] for artist in track.get('artists', [])])
            duration_ms = track.get('duration_ms', 0)
            duration_min = f"{duration_ms // 60000}:{(duration_ms % 60000) // 1000:02d}"
            
            # Add cursor indicator (relative to visible window)
            cursor = "►" if i == self.track_cursor else " "
            highlight = "[bold cyan]" if i == self.track_cursor else ""
            end_highlight = "[/bold cyan]" if i == self.track_cursor else ""
            
            track_num = i + 1
            text += f"{cursor} {highlight}{track_num:3d}. {name}{end_highlight}\n"
            text += f"     👤 {artists} | ⏱️ {duration_min}\n\n"
        
        # Show scroll indicator
        if total_tracks > window_size:
            progress = (self.track_cursor + 1) / total_tracks * 100
            text += f"📍 Track {self.track_cursor + 1}/{total_tracks} ({progress:.0f}%)"
        
        return text
    
    def on_button_pressed(self, event):
        """Handle button presses."""
        screen_name = event.button.id
        self.current_screen = screen_name
        self.update_screen()
        
        # Update button states
        for btn in self.query("Button"):
            if btn.id == screen_name:
                btn.variant = "primary"
            else:
                btn.variant = "default"
    
    def on_key(self, event):
        """Handle key presses."""
        
        # VIM-style navigation in playlists (always active now)
        if event.key == "up" or event.key == "k":
            if self.viewing_tracks:
                if self.current_playlist_tracks:
                    self.track_cursor = (self.track_cursor - 1) % len(self.current_playlist_tracks)
                    self.update_screen()
            else:
                if self.playlists_data:
                    self.playlist_cursor = (self.playlist_cursor - 1) % len(self.playlists_data)
                    self.update_screen()
            event.prevent_default()
        
        elif event.key == "down" or event.key == "j":
            if self.viewing_tracks:
                if self.current_playlist_tracks:
                    self.track_cursor = (self.track_cursor + 1) % len(self.current_playlist_tracks)
                    self.update_screen()
            else:
                if self.playlists_data:
                    self.playlist_cursor = (self.playlist_cursor + 1) % len(self.playlists_data)
                    self.update_screen()
            event.prevent_default()
        
        elif event.key == "enter":
            if self.viewing_tracks:
                self.play_selected_track()
            else:
                self.view_playlist_tracks()
            event.prevent_default()
        
        elif event.key == "escape" or event.key == "b":
            if self.viewing_tracks:
                self.viewing_tracks = False
                self.track_cursor = 0
                self.update_screen()
            event.prevent_default()
        
        elif event.key == "space":
            if self.spotify_client:
                try:
                    if self.is_playing:
                        self.spotify_client.pause_playback()
                    else:
                        self.spotify_client.resume_playback()
                except Exception as e:
                    self.notify(f"Error: {e}")
            event.prevent_default()
        
        elif event.key == "n" or event.key == "right":
            # Skip to next track
            if self.spotify_client:
                try:
                    self.spotify_client.skip_to_next()
                except Exception as e:
                    self.notify(f"Error: {e}")
            event.prevent_default()
        
        elif event.key == "p" or event.key == "left":
            # Skip to previous track (only if not viewing playlists)
            if self.spotify_client and self.current_screen != "playlists":
                try:
                    self.spotify_client.skip_to_previous()
                except Exception as e:
                    self.notify(f"Error: {e}")
            event.prevent_default()
        
        elif event.key == "q":
            self.exit()
    
    def play_selected_playlist(self):
        """Play the currently selected playlist."""
        if not self.spotify_client or not self.playlists_data:
            return
        
        if 0 <= self.playlist_cursor < len(self.playlists_data):
            playlist = self.playlists_data[self.playlist_cursor]
            playlist_name = playlist.get('name', 'Unknown')
            playlist_uri = playlist.get('uri')
            
            if playlist_uri:
                try:
                    # Play the playlist
                    self.spotify_client.sp.start_playback(context_uri=playlist_uri)
                except Exception as e:
                    self.notify(f"❌ Error playing playlist: {e}")
            else:
                self.notify("❌ Playlist URI not found")
    
    @work
    async def view_playlist_tracks(self):
        """Load and view tracks from the selected playlist."""
        if not self.spotify_client or not self.playlists_data:
            return
        
        if 0 <= self.playlist_cursor < len(self.playlists_data):
            playlist = self.playlists_data[self.playlist_cursor]
            playlist_id = playlist.get('id')
            playlist_name = playlist.get('name', 'Unknown')
            
            if playlist_id:
                try:
                    self.notify(f"📚 Loading tracks from {playlist_name}...")
                    tracks = self.spotify_client.get_playlist_tracks(playlist_id)
                    self.current_playlist_tracks = tracks
                    self.viewing_tracks = True
                    self.track_cursor = 0
                    self.tracks_scroll_offset = 0  # Reset scroll position
                    self.update_screen()
                except Exception as e:
                    self.notify(f"❌ Error loading tracks: {e}")
    
    def play_selected_track(self):
        """Play the currently selected track."""
        if not self.spotify_client or not self.current_playlist_tracks:
            return
        
        if 0 <= self.track_cursor < len(self.current_playlist_tracks):
            track_item = self.current_playlist_tracks[self.track_cursor]
            track = track_item.get('track', {})
            track_name = track.get('name', 'Unknown')
            track_uri = track.get('uri')
            
            if track_uri:
                try:
                    # Play the specific track
                    self.spotify_client.sp.start_playback(uris=[track_uri])
                except Exception as e:
                    self.notify(f"❌ Error playing track: {e}")
            else:
                self.notify("❌ Track URI not found")

def main():
    """Main entry point for the spotifytui command."""
    app = SimpleSpotifyTUI()
    app.run()

if __name__ == "__main__":
    main()
