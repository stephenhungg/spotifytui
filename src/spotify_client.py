"""
Spotify API client wrapper using spotipy
"""

import os
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException
from typing import Optional, List, Dict, Any
import logging
from dotenv import load_dotenv
from feature_estimator import AudioFeatureEstimator

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class SpotifyClient:
    """Wrapper for Spotify API operations."""
    
    def __init__(self):
        self.sp = None
        self.feature_estimator = AudioFeatureEstimator()
        self.last_request_time = 0
        self.min_request_interval = 0.5  # Increased to 500ms between requests
        
        # Caching to reduce API calls
        self.cache = {}
        self.cache_ttl = 30  # Cache for 30 seconds
        
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Spotify API."""
        try:
            # Debug: Print environment variables
            client_id = os.getenv('SPOTIPY_CLIENT_ID')
            client_secret = os.getenv('SPOTIPY_CLIENT_SECRET')
            redirect_uri = os.getenv('SPOTIPY_REDIRECT_URI')
            
            
            if not client_id or not client_secret:
                raise ValueError("Missing SPOTIPY_CLIENT_ID or SPOTIPY_CLIENT_SECRET in environment variables")
            
            scope = [
                "user-read-playback-state",
                "user-modify-playback-state",
                "user-read-currently-playing",
                "user-read-playback-position",
                "user-read-recently-played",
                "user-read-email",
                "playlist-read-private",
                "playlist-read-collaborative",
                "user-library-read",
                "user-top-read",
                "user-follow-read"
            ]
            
            # Set up cache directory for tokens
            cache_dir = os.path.expanduser("~/.cache/spotifytui")
            os.makedirs(cache_dir, exist_ok=True)
            cache_path = os.path.join(cache_dir, ".spotify_cache")
            
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                scope=" ".join(scope),
                redirect_uri=redirect_uri or "http://127.0.0.1:8888/callback",
                cache_path=cache_path,
                open_browser=True,
                show_dialog=False
            ))
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    def _rate_limit(self):
        """Ensure we don't exceed rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        self.last_request_time = time.time()
    
    def _safe_api_call(self, func, *args, **kwargs):
        """Make a safe API call with rate limiting and error handling"""
        self._rate_limit()
        try:
            return func(*args, **kwargs)
        except SpotifyException as e:
            if e.http_status == 429:  # Rate limit exceeded
                retry_after = int(e.headers.get('Retry-After', 1))
                logger.warning(f"Rate limit hit, waiting {retry_after} seconds")
                time.sleep(retry_after)
                # Retry once
                self._rate_limit()
                return func(*args, **kwargs)
            else:
                raise e
    
    def get_current_playback(self) -> Optional[Dict[str, Any]]:
        """Get current playback information."""
        try:
            playback = self._safe_api_call(self.sp.current_playback)
            if playback and playback.get('item'):
                track = playback['item']
                logger.debug(f"Current playback: {track.get('name', 'Unknown')} by {', '.join([a['name'] for a in track.get('artists', [])])}")
            return playback
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
            logger.debug(f"Fetching user playlists (limit: {limit})")
            result = self._safe_api_call(self.sp.current_user_playlists, limit=limit)
            playlists = result.get('items', [])
            logger.debug(f"Retrieved {len(playlists)} playlists")
            return playlists
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
    
    def get_audio_features_with_fallback(self, track_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get audio features for a track, with intelligent fallback estimation.
        
        Args:
            track_data: Spotify track object
            
        Returns:
            Dict with audio features (either from API or estimated)
        """
        track_id = track_data.get('id')
        
        if not track_id:
            # No track ID, use estimation
            estimated = self.feature_estimator.estimate_features(track_data)
            return self._track_features_to_dict(estimated)
        
        try:
            # Try the official API first
            audio_features = self._safe_api_call(self.sp.audio_features, [track_id])
            if audio_features and audio_features[0]:
                return audio_features[0]
        except Exception as e:
            logger.debug(f"Audio features API failed for {track_id}: {e}")
        
        # Fallback to estimation
        estimated = self.feature_estimator.estimate_features(track_data)
        return self._track_features_to_dict(estimated)
    
    def _track_features_to_dict(self, features) -> Dict[str, Any]:
        """Convert TrackFeatures object to dict matching Spotify API format"""
        return {
            'danceability': features.danceability,
            'energy': features.energy,
            'valence': features.valence,
            'tempo': features.tempo,
            'acousticness': features.acousticness,
            'instrumentalness': features.instrumentalness,
            'liveness': features.liveness,
            'speechiness': features.speechiness,
            'key': 5,  # Default key (F major)
            'loudness': -10.0,  # Default loudness
            'mode': 1,  # Default major mode
            'time_signature': 4,  # Default 4/4 time
            'duration_ms': features.tempo * 60 * 1000 / 120,  # Rough estimate
        }
