"""
Centralized configuration and constants for spotifytui.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# vibechain API
VIBECHAIN_API_URL: str = os.getenv("VIBECHAIN_API_URL", "http://localhost:8080")
VIBECHAIN_API_PATH: str = os.getenv(
    "VIBECHAIN_API_PATH",
    str(Path.home() / "Documents" / "GitHub" / "playlistify-api"),
)

# update intervals
PLAYBACK_POLL_INTERVAL: float = 10.0  # seconds between spotify API polls
API_RATE_LIMIT_INTERVAL: float = 0.5  # min seconds between API requests

# UI constants
ALBUM_ART_WIDTH: int = 16  # columns (each column = 2 terminal chars)
ALBUM_ART_SAMPLE_SIZE: int = 32  # download and sample from this resolution
PROGRESS_BAR_WIDTH: int = 40
LYRICS_WINDOW_SIZE: int = 25
PLAYLIST_WINDOW_SIZE: int = 15
TRACKS_WINDOW_SIZE: int = 15
MAX_PLAYLISTS: int = 15
MAX_RECENT_TRACKS: int = 10

# demo data for offline mode
DEMO_PLAYLISTS = [
    {
        "name": "Chill Vibes",
        "owner": {"display_name": "Demo User"},
        "tracks": {"total": 25},
        "id": "demo_chill",
        "uri": "spotify:playlist:demo_chill",
    },
    {
        "name": "Workout Mix",
        "owner": {"display_name": "Demo User"},
        "tracks": {"total": 40},
        "id": "demo_workout",
        "uri": "spotify:playlist:demo_workout",
    },
    {
        "name": "Focus Music",
        "owner": {"display_name": "Demo User"},
        "tracks": {"total": 30},
        "id": "demo_focus",
        "uri": "spotify:playlist:demo_focus",
    },
    {
        "name": "Party Hits",
        "owner": {"display_name": "Demo User"},
        "tracks": {"total": 50},
        "id": "demo_party",
        "uri": "spotify:playlist:demo_party",
    },
]

DEMO_TRACKS = {
    "demo_chill": [
        {
            "track": {
                "name": "Midnight City",
                "artists": [{"name": "M83"}],
                "duration_ms": 240000,
                "id": "demo_track_1",
                "uri": "spotify:track:demo_track_1",
            }
        },
        {
            "track": {
                "name": "Breathe Me",
                "artists": [{"name": "Sia"}],
                "duration_ms": 280000,
                "id": "demo_track_2",
                "uri": "spotify:track:demo_track_2",
            }
        },
    ],
    "demo_workout": [
        {
            "track": {
                "name": "Titanium",
                "artists": [{"name": "David Guetta"}, {"name": "Sia"}],
                "duration_ms": 220000,
                "id": "demo_track_3",
                "uri": "spotify:track:demo_track_3",
            }
        },
    ],
}

DEMO_CURRENT_TRACK = {
    "name": "No Active Playback",
    "artists": [{"name": "Demo Mode"}],
    "album": {"name": "Offline"},
    "duration_ms": 210000,
    "popularity": 75,
    "explicit": False,
}

DEMO_LYRICS = """Demo Mode

The Spotify API is currently unavailable.
You can still explore the interface:

  j/k or arrows  navigate playlists
  enter           view tracks
  left/right      scroll lyrics
  space           play/pause
  n/p             next/previous
  s               smart shuffle
  q               quit

The app will reconnect automatically
when the API becomes available again."""
