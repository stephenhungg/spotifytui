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
from src.lyrics_service import LyricsService
import requests
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

class SimpleSpotifyTUI(App):
    """Simple working Spotify TUI."""
    
    TITLE = "Spotify TUI 🎵"
    # Back to clean default styling
    
    current_track = reactive("Loading...")
    current_artist = reactive("")
    current_album = reactive("")
    is_playing = reactive(False)
    track_progress_ms = reactive(0)
    track_duration_ms = reactive(0)
    album_art_url = reactive("")
    track_popularity = reactive(0)
    track_explicit = reactive(False)
    track_release_date = reactive("")
    track_album = reactive("Unknown")
    current_album_art_ascii = ""
    current_screen = reactive("player")
    playlist_cursor = reactive(0)
    track_cursor = reactive(0)
    playlists_data = []
    current_playlist_tracks = []
    viewing_tracks = reactive(False)
    tracks_scroll_offset = reactive(0)
    
    # Lyrics variables
    current_lyrics = reactive("")
    lyrics_source = reactive("")
    current_track_id = reactive("")
    lyrics_scroll_offset = reactive(0)
    
    def __init__(self):
        super().__init__()
        self.spotify_client = None
        self.lyrics_service = LyricsService()
    
    def compose(self) -> ComposeResult:
        yield Header()
        
        with Container():
            # Main content with everything side by side
            with Horizontal():
                # Left side - Player
                with Container(id="player-section", classes="player-panel"):
                    yield Static(id="player-content")
                
                # Middle - Playlists
                with Container(id="playlist-section", classes="playlist-panel"):
                    yield Static(id="playlist-content")
                
                # Right side - Lyrics
                with Container(id="lyrics-section", classes="lyrics-panel"):
                    yield Static(id="lyrics-content")
            

        
        yield Footer()
    
    def on_mount(self):
        """Initialize the app."""
        self.init_spotify()
        self.update_screen()
        self.set_interval(2, self.update_music)
        
        # Add help text to footer
        footer = self.query_one("Footer")
        footer.text = "🎮 j/k: Navigate Playlists | ←→: Scroll Lyrics | L: Loop Lyrics | Enter: Select/Play | Space: Play/Pause | N/P: Skip | Q: Quit"
    
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
        
        # If we have a client but no playlists data, try to load them
        if not hasattr(self, 'playlists_data') or not self.playlists_data:
            try:
                playlists = self.spotify_client.get_user_playlists()
                if playlists:
                    self.playlists_data = playlists[:15]
                    self.update_screen()  # Refresh the display
            except Exception:
                pass  # Ignore errors, will retry next time
        
        try:
            playback = self.spotify_client.get_current_playback()
            if playback and playback.get('item'):
                track = playback['item']
                track_id = track.get('id', '')
                self.current_track = track.get('name', 'Unknown')
                self.current_artist = ', '.join([a['name'] for a in track.get('artists', [])])
                self.current_album = track.get('album', {}).get('name', 'Unknown')
                self.is_playing = playback.get('is_playing', False)
                self.track_progress_ms = playback.get('progress_ms', 0)
                self.track_duration_ms = track.get('duration_ms', 0)
                
                # Get additional track info
                self.track_popularity = track.get('popularity', 0)
                self.track_explicit = track.get('explicit', False)
                album_info = track.get('album', {})
                self.track_release_date = album_info.get('release_date', 'Unknown')
                self.track_album = album_info.get('name', 'Unknown')
                
                # Check if track changed for lyrics
                if track_id != self.current_track_id:
                    self.current_track_id = track_id
                    self.fetch_lyrics_for_current_track()
                
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
    

    
    @work
    async def fetch_lyrics_for_current_track(self):
        """Fetch lyrics for the currently playing track."""
        if not self.current_track or self.current_track == "No music playing":
            return
        
        try:
            self.lyrics_source = "🔍 Searching..."
            self.current_lyrics = "🔍 Searching for lyrics..."
            self.update_screen()
            
            lyrics, source = self.lyrics_service.get_lyrics(self.current_artist, self.current_track)
            if lyrics:
                self.current_lyrics = lyrics
                self.lyrics_source = source
            else:
                self.current_lyrics = f"❌ No lyrics found for:\n{self.current_track}\nby {self.current_artist}"
                self.lyrics_source = "Not found"
            
            self.lyrics_scroll_offset = 0  # Reset scroll when new lyrics load
            self.update_screen()
        except Exception as e:
            self.current_lyrics = f"❌ Error fetching lyrics: {e}"
            self.lyrics_source = "Error"
            self.update_screen()
    
    def update_screen(self):
        """Update all three panels simultaneously."""
        # Update player panel
        player_content = self.query_one("#player-content")
        player_content.update(self.get_player_display())
        
        # Update playlist panel
        playlist_content = self.query_one("#playlist-content")
        if self.viewing_tracks:
            playlist_content.update(self.get_tracks_view())
        else:
            playlist_content.update(self.get_playlists_text())
        
        # Update lyrics panel
        lyrics_content = self.query_one("#lyrics-content")
        lyrics_content.update(self.get_lyrics_display())
    
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
        
        # Track info section
        explicit_badge = "🅴" if self.track_explicit else ""
        release_year = self.track_release_date[:4] if len(self.track_release_date) >= 4 else "Unknown"
        
        # Format track info properly (accounting for emoji space)
        track_name = self.current_track[:46] if len(self.current_track) <= 46 else self.current_track[:43] + "..."
        artist_name = self.current_artist[:51] if len(self.current_artist) <= 51 else self.current_artist[:48] + "..."
        album_name = self.current_album[:51] if len(self.current_album) <= 51 else self.current_album[:48] + "..."
        
        # Format stats properly
        popularity_text = f"{self.track_popularity}/100"
        album_text = self.track_album[:44] if len(self.track_album) <= 44 else self.track_album[:41] + "..."
        
        # Create the display with enhanced track info
        text = f"""
🎵 SPOTIFY TUI - {status_text} {status_icon}

{album_art}

╔══════════════════════════════════════════════════════════════╗
║ 🎵 {track_name:<46}{explicit_badge:<3}
║ 👤 {artist_name:<51}
║ 💿 {album_name:<51}
║                                                              
║ 📊 TRACK INFO                                                
║ 📅 Released: {release_year:<8} 🔥 Popularity: {popularity_text:<10}    
║ 💿 Album: {album_text:<44}
╠══════════════════════════════════════════════════════════════╣
║ {progress_time} [{progress_bar}] {duration_time}             
║ Progress: {progress_ratio * 100:.1f}%{'':<38}               
╚══════════════════════════════════════════════════════════════╝

Controls:
Space - Play/Pause | N - Next Track | P - Previous Track | ←→ - Scroll Lyrics | Q - Quit
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
        if not self.spotify_client:
            return "📚 PLAYLISTS\n\n❌ Not connected to Spotify"
        
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
            text += "Use ↑↓/j/k to navigate, Enter to view tracks, Shift+P to play playlist\n\n"
            
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
    
    def get_lyrics_display(self):
        """Display lyrics for the current song with scrolling."""
        if not self.current_track or self.current_track == "No music playing":
            return """
📝 LYRICS

🎵 No music playing

Start playing a song to see lyrics here!
Use ↑↓/j/k to scroll, 1-3 to switch screens, Q to quit
"""
        
        # Header with current track info
        header = f"""📝 LYRICS - {self.lyrics_source}

🎵 {self.current_track}
👤 {self.current_artist}
💿 {self.current_album}

────────────────────────────────────────────────────────────────
"""
        
        if not self.current_lyrics:
            return header + "\n🔍 Loading lyrics...\n"
        
        # Split lyrics into lines for scrolling
        lyrics_lines = self.current_lyrics.split('\n')
        
        # Calculate scrolling window (show 20 lines at a time)
        window_size = 20
        total_lines = len(lyrics_lines)
        
        # Make sure scroll offset doesn't go out of bounds
        max_scroll = max(0, total_lines - window_size)
        self.lyrics_scroll_offset = max(0, min(self.lyrics_scroll_offset, max_scroll))
        
        start_idx = self.lyrics_scroll_offset
        end_idx = min(start_idx + window_size, total_lines)
        
        # Build the display
        display_lines = lyrics_lines[start_idx:end_idx]
        lyrics_content = '\n'.join(display_lines)
        
        # Add scroll indicator
        footer = "\n────────────────────────────────────────────────────────────────\n"
        if total_lines > window_size:
            progress = (start_idx + 1) / total_lines * 100
            footer += f"📍 Lines {start_idx + 1}-{end_idx} of {total_lines} ({progress:.0f}%) | ←→ to scroll"
        else:
            footer += "Use ←→ arrows to scroll lyrics"
        
        return header + lyrics_content + footer
    

    
    def on_key(self, event):
        """Handle key presses."""
        
        # Playlist navigation
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
        
        # Lyrics scrolling with L key
        elif event.key == "l":
            # Toggle lyrics scroll mode or scroll down
            lyrics_lines = self.current_lyrics.split('\n') if self.current_lyrics else []
            max_scroll = max(0, len(lyrics_lines) - 20)
            if self.lyrics_scroll_offset < max_scroll:
                self.lyrics_scroll_offset += 1
            else:
                self.lyrics_scroll_offset = 0  # Loop back to top
            self.update_screen()
            event.prevent_default()
        
        elif event.key == "enter":
            if self.viewing_tracks:
                self.play_selected_track()
            else:
                self.view_playlist_tracks()
            event.prevent_default()
        
        # Play playlist (P key in playlist view)
        elif event.key == "P":
            if not self.viewing_tracks:
                self.play_selected_playlist()
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
        
        elif event.key == "n":
            # Skip to next track
            if self.spotify_client:
                try:
                    self.spotify_client.skip_to_next()
                except Exception as e:
                    self.notify(f"Error: {e}")
            event.prevent_default()
        
        elif event.key == "p":
            # Skip to previous track
            if self.spotify_client:
                try:
                    self.spotify_client.skip_to_previous()
                except Exception as e:
                    self.notify(f"Error: {e}")
            event.prevent_default()
        
        # Left/Right arrow keys for lyrics scrolling
        elif event.key == "left":
            # Scroll lyrics up
            if self.lyrics_scroll_offset > 0:
                self.lyrics_scroll_offset -= 1
                self.update_screen()
            event.prevent_default()
        
        elif event.key == "right":
            # Scroll lyrics down
            lyrics_lines = self.current_lyrics.split('\n') if self.current_lyrics else []
            max_scroll = max(0, len(lyrics_lines) - 20)
            if self.lyrics_scroll_offset < max_scroll:
                self.lyrics_scroll_offset += 1
                self.update_screen()
            event.prevent_default()
        
        elif event.key == "q":
            self.exit()
    
    def play_selected_playlist(self):
        """Play the currently selected playlist from the beginning."""
        if not self.spotify_client or not self.playlists_data:
            return
        
        if 0 <= self.playlist_cursor < len(self.playlists_data):
            playlist = self.playlists_data[self.playlist_cursor]
            playlist_name = playlist.get('name', 'Unknown')
            playlist_uri = playlist.get('uri')
            
            if playlist_uri:
                try:
                    # Play the playlist from the beginning
                    self.spotify_client.sp.start_playback(context_uri=playlist_uri)
                    self.notify(f"🎵 Playing playlist '{playlist_name}'")
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
        """Play the currently selected track within the playlist context."""
        if not self.spotify_client or not self.current_playlist_tracks:
            return
        
        if 0 <= self.track_cursor < len(self.current_playlist_tracks):
            track_item = self.current_playlist_tracks[self.track_cursor]
            track = track_item.get('track', {})
            track_name = track.get('name', 'Unknown')
            track_uri = track.get('uri')
            
            # Get the current playlist info
            if self.playlists_data and 0 <= self.playlist_cursor < len(self.playlists_data):
                playlist = self.playlists_data[self.playlist_cursor]
                playlist_uri = playlist.get('uri')
                
                if track_uri and playlist_uri:
                    try:
                        # Play the track within the playlist context, starting from the selected track
                        self.spotify_client.sp.start_playback(
                            context_uri=playlist_uri,
                            offset={"position": self.track_cursor}
                        )
                        self.notify(f"🎵 Playing '{track_name}' from playlist")
                    except Exception as e:
                        self.notify(f"❌ Error playing track: {e}")
                else:
                    self.notify("❌ Track or playlist URI not found")
            else:
                self.notify("❌ No playlist selected")

def main():
    """Main entry point for the spotifytui command."""
    app = SimpleSpotifyTUI()
    app.run()

if __name__ == "__main__":
    main()
