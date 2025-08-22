"""
Screen components for the Spotify TUI
"""

from textual.app import App
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import (
    Static, Button, Label, DataTable, Input, Select, 
    ProgressBar, RichLog, Header
)
from textual.reactive import reactive
from textual import work
from textual import events
from typing import List, Dict, Any, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)

class PlayerScreen(Static):
    """Main player screen with playback controls."""
    
    current_track = reactive("No track playing")
    current_artist = reactive("")
    current_album = reactive("")
    is_playing = reactive(False)
    progress = reactive(0.0)
    volume = reactive(50)
    
    def compose(self) -> None:
        """Compose the player screen."""
        with Container(id="player-container"):
            yield Header("🎵 Now Playing", classes="screen-header")
            
            with Container(id="track-info"):
                yield Label("Track:", classes="label")
                yield Label(self.current_track, id="track-name", classes="track-name")
                yield Label("Artist:", classes="label")
                yield Label(self.current_artist, id="artist-name", classes="artist-name")
                yield Label("Album:", classes="label")
                yield Label(self.current_album, id="album-name", classes="album-name")
            
            with Container(id="playback-controls"):
                yield Button("⏮️ Previous", id="btn-previous", classes="control-btn")
                yield Button("⏯️ Play/Pause", id="btn-play-pause", classes="control-btn")
                yield Button("⏭️ Next", id="btn-next", classes="control-btn")
                yield Button("⏹️ Stop", id="btn-stop", classes="control-btn")
            
            with Container(id="progress-container"):
                yield Label("Progress:", classes="label")
                yield ProgressBar(total=100, id="progress-bar")
            
            with Container(id="volume-container"):
                yield Label("Volume:", classes="label")
                yield ProgressBar(total=100, id="volume-bar")
                yield Button("🔊 Volume Up", id="btn-volume-up", classes="control-btn")
                yield Button("🔇 Volume Down", id="btn-volume-down", classes="control-btn")
            
            with Container(id="device-info"):
                yield Label("Available Devices:", classes="label")
                yield DataTable(id="devices-table")
    
    def on_mount(self) -> None:
        """Initialize the player screen."""
        self.start_playback_update()
    
    def on_focus(self, event: events.Focus) -> None:
        """Handle focus events for visual feedback."""
        if hasattr(event.widget, 'add_class'):
            event.widget.add_class("focused")
    
    def on_blur(self, event: events.Blur) -> None:
        """Handle blur events for visual feedback."""
        if hasattr(event.widget, 'remove_class'):
            event.widget.remove_class("focused")
    
    @work
    async def start_playback_update(self):
        """Start periodic playback updates."""
        while True:
            await self.update_playback_info()
            await asyncio.sleep(2)
    
    async def update_playback_info(self):
        """Update playback information from Spotify."""
        app = self.app
        if not app or not hasattr(app, 'get_spotify_client'):
            print("No app or get_spotify_client method")
            return
        
        client = app.get_spotify_client()
        if not client:
            print("No Spotify client available")
            return
        
        try:
            print("Fetching playback info...")  # Debug
            playback = client.get_current_playback()
            print(f"Playback response: {playback}")  # Debug
            
            if playback and playback.get('item'):
                track = playback['item']
                self.current_track = track.get('name', 'Unknown Track')
                self.current_artist = ', '.join([artist['name'] for artist in track.get('artists', [])])
                self.current_album = track.get('album', {}).get('name', 'Unknown Album')
                self.is_playing = playback.get('is_playing', False)
                
                print(f"Track: {self.current_track}")  # Debug
                print(f"Artist: {self.current_artist}")  # Debug
                print(f"Album: {self.current_album}")  # Debug
                
                # Update progress
                if playback.get('progress_ms') and track.get('duration_ms'):
                    progress_ms = playback['progress_ms']
                    duration_ms = track['duration_ms']
                    progress_percent = (progress_ms / duration_ms) * 100
                    # Update progress bar using advance method
                    progress_bar = self.query_one("#progress-bar")
                    if progress_bar:
                        progress_bar.advance(progress_percent - self.progress)
                        self.progress = progress_percent
                
                # Update volume
                if playback.get('device'):
                    new_volume = playback['device'].get('volume_percent', 50)
                    # Update volume bar using advance method
                    volume_bar = self.query_one("#volume-bar")
                    if volume_bar:
                        volume_bar.advance(new_volume - self.volume)
                        self.volume = new_volume
            else:
                print("No playback or no track item")  # Debug
                self.current_track = "No track playing"
                self.current_artist = ""
                self.current_album = ""
        except Exception as e:
            print(f"Error updating playback: {e}")  # Debug
            logger.error(f"Failed to update playback info: {e}")

class PlaylistsScreen(Static):
    """Screen for displaying and managing playlists."""
    
    def compose(self) -> None:
        """Compose the playlists screen."""
        with Container(id="playlists-container"):
            yield Header("📚 Your Playlists", classes="screen-header")
            
            with Container(id="playlists-controls"):
                yield Button("🔄 Refresh", id="btn-refresh-playlists", classes="control-btn")
                yield Button("➕ New Playlist", id="btn-new-playlist", classes="control-btn")
            
            yield DataTable(id="playlists-table")
    
    def on_mount(self) -> None:
        """Initialize the playlists screen."""
        self.load_playlists()
    
    def on_focus(self, event: events.Focus) -> None:
        """Handle focus events for visual feedback."""
        if hasattr(event.widget, 'add_class'):
            event.widget.add_class("focused")
    
    def on_blur(self, event: events.Blur) -> None:
        """Handle blur events for visual feedback."""
        if hasattr(event.widget, 'remove_class'):
            event.widget.remove_class("focused")
    
    @work
    async def load_playlists(self):
        """Load user playlists from Spotify."""
        app = self.app
        if not app or not hasattr(app, 'get_spotify_client'):
            return
        
        client = app.get_spotify_client()
        if not client:
            return
        
        try:
            playlists = client.get_user_playlists()
            table = self.query_one("#playlists-table")
            table.clear()
            table.add_columns("Name", "Owner", "Tracks", "Public")
            
            for playlist in playlists:
                table.add_row(
                    playlist.get('name', 'Unknown'),
                    playlist.get('owner', {}).get('display_name', 'Unknown'),
                    str(playlist.get('tracks', {}).get('total', 0)),
                    "Yes" if playlist.get('public', False) else "No"
                )
        except Exception as e:
            logger.error(f"Failed to load playlists: {e}")

class SearchScreen(Static):
    """Screen for searching Spotify content."""
    
    def compose(self) -> None:
        """Compose the search screen."""
        with Container(id="search-container"):
            yield Header("🔍 Search Spotify", classes="screen-header")
            
            with Container(id="search-controls"):
                yield Input(placeholder="Enter search query...", id="search-input")
                yield Select(
                    options=[
                        ("Tracks", "track"),
                        ("Artists", "artist"),
                        ("Albums", "album"),
                        ("Playlists", "playlist")
                    ],
                    value="track",
                    id="search-type"
                )
                yield Button("🔍 Search", id="btn-search", classes="control-btn")
            
            yield DataTable(id="search-results")
    
    def on_focus(self, event: events.Focus) -> None:
        """Handle focus events for visual feedback."""
        if hasattr(event.widget, 'add_class'):
            event.widget.add_class("focused")
    
    def on_blur(self, event: events.Blur) -> None:
        """Handle blur events for visual feedback."""
        if hasattr(event.widget, 'remove_class'):
            event.widget.remove_class("focused")
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle search button press."""
        if event.button.id == "btn-search":
            self.perform_search()
    
    def perform_search(self):
        """Perform the search operation."""
        search_input = self.query_one("#search-input")
        search_type = self.query_one("#search-type")
        
        query = search_input.value
        search_type_value = search_type.value
        
        if not query:
            return
        
        self.execute_search(query, search_type_value)
    
    @work
    async def execute_search(self, query: str, search_type: str):
        """Execute the search on Spotify."""
        app = self.app
        if not app or not hasattr(app, 'get_spotify_client'):
            return
        
        client = app.get_spotify_client()
        if not client:
            return
        
        try:
            results = client.search(query, search_type)
            table = self.query_one("#search-results")
            table.clear()
            
            if search_type == "track":
                table.add_columns("Title", "Artist", "Album", "Duration")
                for track in results.get('tracks', {}).get('items', []):
                    duration_ms = track.get('duration_ms', 0)
                    duration_min = f"{duration_ms // 60000}:{(duration_ms % 60000) // 1000:02d}"
                    table.add_row(
                        track.get('name', 'Unknown'),
                        ', '.join([artist['name'] for artist in track.get('artists', [])]),
                        track.get('album', {}).get('name', 'Unknown'),
                        duration_min
                    )
            elif search_type == "artist":
                table.add_columns("Name", "Genres", "Popularity")
                for artist in results.get('artists', {}).get('items', []):
                    table.add_row(
                        artist.get('name', 'Unknown'),
                        ', '.join(artist.get('genres', [])[:3]),
                        str(artist.get('popularity', 0))
                    )
            elif search_type == "album":
                table.add_columns("Title", "Artist", "Release Date", "Tracks")
                for album in results.get('albums', {}).get('items', []):
                    table.add_row(
                        album.get('name', 'Unknown'),
                        ', '.join([artist['name'] for artist in album.get('artists', [])]),
                        album.get('release_date', 'Unknown'),
                        str(album.get('total_tracks', 0))
                    )
            elif search_type == "playlist":
                table.add_columns("Name", "Owner", "Tracks", "Description")
                for playlist in results.get('playlists', {}).get('items', []):
                    table.add_row(
                        playlist.get('name', 'Unknown'),
                        playlist.get('owner', {}).get('display_name', 'Unknown'),
                        str(playlist.get('tracks', {}).get('total', 0)),
                        playlist.get('description', '')[:50] + '...' if playlist.get('description') else ''
                    )
        except Exception as e:
            logger.error(f"Search failed: {e}")

class ArtistScreen(Static):
    """Screen for displaying artist information."""
    
    def compose(self) -> None:
        """Compose the artist screen."""
        with Container(id="artist-container"):
            yield Header("👤 Artist Information", classes="screen-header")
            
            with Container(id="artist-info"):
                yield Label("Select an artist from search results", id="artist-name", classes="artist-name")
                yield Label("", id="artist-genres", classes="artist-genres")
                yield Label("", id="artist-popularity", classes="artist-popularity")
            
            yield DataTable(id="artist-albums")
    
    def display_artist(self, artist_data: Dict[str, Any]):
        """Display artist information."""
        name_label = self.query_one("#artist-name")
        genres_label = self.query_one("#artist-genres")
        popularity_label = self.query_one("#artist-popularity")
        
        name_label.update(f"👤 {artist_data.get('name', 'Unknown Artist')}")
        genres_label.update(f"Genres: {', '.join(artist_data.get('genres', []))}")
        popularity_label.update(f"Popularity: {artist_data.get('popularity', 0)}/100")
        
        self.load_artist_albums(artist_data.get('id'))
    
    @work
    async def load_artist_albums(self, artist_id: str):
        """Load albums by the artist."""
        if not artist_id:
            return
        
        app = self.app
        if not app or not hasattr(app, 'get_spotify_client'):
            return
        
        client = app.get_spotify_client()
        if not client:
            return
        
        try:
            albums = client.get_artist_albums(artist_id)
            table = self.query_one("#artist-albums")
            table.clear()
            table.add_columns("Album", "Release Date", "Tracks", "Type")
            
            for album in albums:
                table.add_row(
                    album.get('name', 'Unknown'),
                    album.get('release_date', 'Unknown'),
                    str(album.get('total_tracks', 0)),
                    album.get('album_type', 'Unknown')
                )
        except Exception as e:
            logger.error(f"Failed to load artist albums: {e}")

class AlbumScreen(Static):
    """Screen for displaying album information."""
    
    def compose(self) -> None:
        """Compose the album screen."""
        with Container(id="album-container"):
            yield Header("💿 Album Information", classes="screen-header")
            
            with Container(id="album-info"):
                yield Label("Select an album from search results", id="album-name", classes="album-name")
                yield Label("", id="album-artist", classes="album-artist")
                yield Label("", id="album-release", classes="album-release")
                yield Label("", id="album-tracks", classes="album-tracks")
            
            yield DataTable(id="album-tracks-table")
    
    def display_album(self, album_data: Dict[str, Any]):
        """Display album information."""
        name_label = self.query_one("#album-name")
        artist_label = self.query_one("#album-artist")
        release_label = self.query_one("#album-release")
        tracks_label = self.query_one("#album-tracks")
        
        name_label.update(f"💿 {album_data.get('name', 'Unknown Album')}")
        artist_label.update(f"Artist: {', '.join([artist['name'] for artist in album_data.get('artists', [])])}")
        release_label.update(f"Release Date: {album_data.get('release_date', 'Unknown')}")
        tracks_label.update(f"Total Tracks: {album_data.get('total_tracks', 0)}")
        
        self.load_album_tracks(album_data.get('id'))
    
    @work
    async def load_album_tracks(self, album_id: str):
        """Load tracks from the album."""
        if not album_id:
            return
        
        app = self.app
        if not app or not hasattr(app, 'get_spotify_client'):
            return
        
        client = app.get_spotify_client()
        if not client:
            return
        
        try:
            tracks = client.get_album_tracks(album_id)
            table = self.query_one("#album-tracks-table")
            table.clear()
            table.add_columns("Track", "Duration", "Explicit")
            
            for track in tracks:
                duration_ms = track.get('duration_ms', 0)
                duration_min = f"{duration_ms // 60000}:{(duration_ms % 60000) // 1000:02d}"
                table.add_row(
                    track.get('name', 'Unknown'),
                    duration_min,
                    "Yes" if track.get('explicit', False) else "No"
                )
        except Exception as e:
            logger.error(f"Failed to load album tracks: {e}")

class LyricsScreen(Static):
    """Screen for displaying song lyrics."""
    
    def compose(self) -> None:
        """Compose the lyrics screen."""
        with Container(id="lyrics-container"):
            yield Header("📝 Song Lyrics", classes="screen-header")
            
            with Container(id="lyrics-info"):
                yield Label("Currently playing track lyrics will appear here", id="lyrics-track", classes="lyrics-track")
                yield Label("", id="lyrics-artist", classes="lyrics-artist")
            
            yield RichLog(id="lyrics-content", classes="lyrics-content")
            
            with Container(id="lyrics-controls"):
                yield Button("🔄 Refresh", id="btn-refresh-lyrics", classes="control-btn")
                yield Button("📋 Copy", id="btn-copy-lyrics", classes="control-btn")
    
    def on_mount(self) -> None:
        """Initialize the lyrics screen."""
        self.start_lyrics_update()
    
    def on_focus(self, event: events.Focus) -> None:
        """Handle focus events for visual feedback."""
        if hasattr(event.widget, 'add_class'):
            event.widget.add_class("focused")
    
    def on_blur(self, event: events.Blur) -> None:
        """Handle blur events for visual feedback."""
        if hasattr(event.widget, 'remove_class'):
            event.widget.remove_class("focused")
    
    @work
    async def start_lyrics_update(self):
        """Start periodic lyrics updates."""
        while True:
            await self.update_lyrics()
            await asyncio.sleep(5)
    
    async def update_lyrics(self):
        """Update lyrics for the currently playing track."""
        app = self.app
        if not app or not hasattr(app, 'get_spotify_client'):
            return
        
        client = app.get_spotify_client()
        if not client:
            return
        
        try:
            playback = client.get_current_playback()
            if playback and playback.get('item'):
                track = playback['item']
                track_name = track.get('name', 'Unknown Track')
                artist_name = ', '.join([artist['name'] for artist in track.get('artists', [])])
                
                track_label = self.query_one("#lyrics-track")
                artist_label = self.query_one("#lyrics-artist")
                lyrics_content = self.query_one("#lyrics-content")
                
                track_label.update(f"📝 {track_name}")
                artist_label.update(f"Artist: {artist_name}")
                
                # For now, we'll show a placeholder since Spotify doesn't provide lyrics via API
                # In a real implementation, you'd need to integrate with a lyrics service
                lyrics_content.write(f"[bold]Lyrics for: {track_name}[/bold]\n")
                lyrics_content.write(f"[italic]by {artist_name}[/italic]\n\n")
                lyrics_content.write("Lyrics are not available through the Spotify API.\n")
                lyrics_content.write("To get lyrics, you would need to integrate with a lyrics service\n")
                lyrics_content.write("like Genius, Musixmatch, or similar.\n\n")
                lyrics_content.write("This is a placeholder for the lyrics functionality.")
        except Exception as e:
            logger.error(f"Failed to update lyrics: {e}")
