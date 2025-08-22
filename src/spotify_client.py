"""
Spotify API client wrapper using spotipy
"""

import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from typing import Optional, List, Dict, Any
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class SpotifyClient:
    """Wrapper for Spotify API operations."""
    
    def __init__(self):
        self.sp = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Spotify API."""
        try:
            # Debug: Print environment variables
            client_id = os.getenv('SPOTIPY_CLIENT_ID')
            client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
            redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
            
            logger.info(f"Client ID: {client_id[:10] if client_id else 'None'}...")
            logger.info(f"Client Secret: {client_secret[:10] if client_secret else 'None'}...")
            logger.info(f"Redirect URI: {redirect_uri}")
            
            if not client_id or not client_secret:
                raise ValueError("Missing SPOTIPY_CLIENT_ID or SPOTIPY_CLIENT_SECRET in environment variables")
            
            scope = [
                "user-read-playback-state",
                "user-modify-playback-state",
                "user-read-currently-playing",
                "user-read-playback-position",
                "user-read-recently-played",
                "user-read-playback-state",
                "user-read-email",
                "playlist-read-private",
                "playlist-read-collaborative",
                "user-library-read",
                "user-top-read",
                "user-read-recently-played",
                "user-follow-read"
            ]
            
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                scope=" ".join(scope),
                redirect_uri=redirect_uri or "http://127.0.0.1:8888/callback"
            ))
            logger.info("Successfully authenticated with Spotify")
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    def get_current_playback(self) -> Optional[Dict[str, Any]]:
        """Get current playback information."""
        try:
            return self.sp.current_playback()
        except Exception as e:
            logger.error(f"Failed to get current playback: {e}")
            return None
    
    def get_available_devices(self) -> List[Dict[str, Any]]:
        """Get available playback devices."""
        try:
            result = self.sp.devices()
            return result.get('devices', [])
        except Exception as e:
            logger.error(f"Failed to get devices: {e}")
            return []
    
    def play_track(self, track_uri: str, device_id: Optional[str] = None):
        """Play a specific track."""
        try:
            self.sp.start_playback(device_id=device_id, uris=[track_uri])
        except Exception as e:
            logger.error(f"Failed to play track: {e}")
    
    def pause_playback(self, device_id: Optional[str] = None):
        """Pause current playback."""
        try:
            self.sp.pause_playback(device_id=device_id)
        except Exception as e:
            logger.error(f"Failed to pause playback: {e}")
    
    def resume_playback(self, device_id: Optional[str] = None):
        """Resume current playback."""
        try:
            self.sp.start_playback(device_id=device_id)
        except Exception as e:
            logger.error(f"Failed to resume playback: {e}")
    
    def skip_to_next(self, device_id: Optional[str] = None):
        """Skip to next track."""
        try:
            self.sp.next_track(device_id=device_id)
        except Exception as e:
            logger.error(f"Failed to skip to next: {e}")
    
    def skip_to_previous(self, device_id: Optional[str] = None):
        """Skip to previous track."""
        try:
            self.sp.previous_track(device_id=device_id)
        except Exception as e:
            logger.error(f"Failed to skip to previous: {e}")
    
    def set_volume(self, volume_percent: int, device_id: Optional[str] = None):
        """Set playback volume."""
        try:
            self.sp.volume(volume_percent, device_id=device_id)
        except Exception as e:
            logger.error(f"Failed to set volume: {e}")
    
    def search(self, query: str, type: str = "track", limit: int = 20) -> Dict[str, Any]:
        """Search for tracks, artists, albums, or playlists."""
        try:
            return self.sp.search(q=query, type=type, limit=limit)
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {}
    
    def get_user_playlists(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user's playlists."""
        try:
            result = self.sp.current_user_playlists(limit=limit)
            return result.get('items', [])
        except Exception as e:
            logger.error(f"Failed to get playlists: {e}")
            return []
    
    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get tracks from a playlist."""
        try:
            result = self.sp.playlist_tracks(playlist_id, limit=limit)
            return result.get('items', [])
        except Exception as e:
            logger.error(f"Failed to get playlist tracks: {e}")
            return []
    
    def get_artist_albums(self, artist_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get albums by an artist."""
        try:
            result = self.sp.artist_albums(artist_id, limit=limit)
            return result.get('items', [])
        except Exception as e:
            logger.error(f"Failed to get artist albums: {e}")
            return []
    
    def get_album_tracks(self, album_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get tracks from an album."""
        try:
            result = self.sp.album_tracks(album_id, limit=limit)
            return result.get('items', [])
        except Exception as e:
            logger.error(f"Failed to get album tracks: {e}")
            return []
    
    def get_recently_played(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recently played tracks."""
        try:
            result = self.sp.current_user_recently_played(limit=limit)
            return result.get('items', [])
        except Exception as e:
            logger.error(f"Failed to get recently played: {e}")
            return []
