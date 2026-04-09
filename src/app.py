"""
Main Textual application for spotifytui.
"""

import logging

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Container
from textual.widgets import Header, Footer
from textual.reactive import reactive
from textual import work

from spotify_client import SpotifyClient
from lyrics_service import LyricsService
from vibechain_client import VibeChainClient, TrackFeatures
from album_art import download_album_art, render_album_art, DEFAULT_ART
from widgets.player import PlayerWidget
from widgets.playlists import PlaylistWidget
from widgets.lyrics import LyricsWidget
from config import (
    PLAYBACK_POLL_INTERVAL,
    MAX_PLAYLISTS,
    MAX_RECENT_TRACKS,
    DEMO_PLAYLISTS,
    DEMO_TRACKS,
    DEMO_CURRENT_TRACK,
    DEMO_LYRICS,
)

logger = logging.getLogger(__name__)


class SpotifyTUI(App):
    """Spotify terminal UI with lyrics and AI recommendations."""

    TITLE = "spotifytui"
    CSS_PATH = "spotifytui.tcss"

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("space", "toggle_playback", "Play/Pause"),
        ("n", "next_track", "Next"),
        ("p", "prev_track", "Previous"),
        ("s", "smart_shuffle", "Smart Shuffle"),
    ]

    # playback state
    current_track: reactive[str] = reactive("Loading...")
    current_artist: reactive[str] = reactive("")
    current_album: reactive[str] = reactive("")
    is_playing: reactive[bool] = reactive(False)
    track_progress_ms: reactive[int] = reactive(0)
    track_duration_ms: reactive[int] = reactive(0)
    track_popularity: reactive[int] = reactive(0)
    track_explicit: reactive[bool] = reactive(False)
    track_release_date: reactive[str] = reactive("")

    # navigation state
    playlist_cursor: reactive[int] = reactive(0)
    track_cursor: reactive[int] = reactive(0)
    viewing_tracks: reactive[bool] = reactive(False)
    tracks_scroll_offset: reactive[int] = reactive(0)

    # lyrics state
    current_lyrics: reactive[str] = reactive("")
    lyrics_source: reactive[str] = reactive("")
    current_track_id: reactive[str] = reactive("")
    lyrics_scroll_offset: reactive[int] = reactive(0)

    # AI state
    ai_enabled: reactive[bool] = reactive(True)
    ai_prediction: reactive[str] = reactive("")

    # offline state
    offline_mode: reactive[bool] = reactive(False)

    def __init__(self) -> None:
        super().__init__()
        self.spotify_client: SpotifyClient | None = None
        self.lyrics_service = LyricsService()
        self.vibechain_client = VibeChainClient()

        self.playlists_data: list[dict] = []
        self.current_playlist_tracks: list[dict] = []
        self.recent_tracks: list[TrackFeatures] = []
        self.ai_recommendations: list[dict] = []
        self.album_art_ascii: str = DEFAULT_ART
        self.album_art_url: str = ""
        self.api_error_count: int = 0

    # ── layout ──────────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        yield Header()
        with Horizontal(id="main-container"):
            yield PlayerWidget(id="player-section")
            yield PlaylistWidget(id="playlist-section")
            yield LyricsWidget(id="lyrics-section")
        yield Footer()

    def on_mount(self) -> None:
        self.init_spotify()
        self.refresh_display()
        self.set_interval(PLAYBACK_POLL_INTERVAL, self.poll_playback)

    # ── display refresh ─────────────────────────────────────────────

    def refresh_display(self) -> None:
        """Push current state into each widget."""
        player = self.query_one("#player-section", PlayerWidget)
        player.update(
            player.render_player(
                track=self.current_track,
                artist=self.current_artist,
                album=self.current_album,
                is_playing=self.is_playing,
                progress_ms=self.track_progress_ms,
                duration_ms=self.track_duration_ms,
                popularity=self.track_popularity,
                explicit=self.track_explicit,
                release_date=self.track_release_date,
                album_art_ascii=self.album_art_ascii,
                ai_prediction=self.ai_prediction,
                offline=self.offline_mode,
            )
        )

        playlist_widget = self.query_one("#playlist-section", PlaylistWidget)
        if self.viewing_tracks:
            playlist_name = ""
            if self.playlists_data and 0 <= self.playlist_cursor < len(self.playlists_data):
                playlist_name = self.playlists_data[self.playlist_cursor].get("name", "")
            playlist_widget.update(
                playlist_widget.render_tracks(
                    tracks=self.current_playlist_tracks,
                    cursor=self.track_cursor,
                    scroll_offset=self.tracks_scroll_offset,
                    playlist_name=playlist_name,
                )
            )
        else:
            playlist_widget.update(
                playlist_widget.render_playlists(
                    playlists=self.playlists_data,
                    cursor=self.playlist_cursor,
                    offline=self.offline_mode,
                )
            )

        lyrics_widget = self.query_one("#lyrics-section", LyricsWidget)
        lyrics_widget.update(
            lyrics_widget.render_lyrics(
                lyrics=self.current_lyrics,
                source=self.lyrics_source,
                track=self.current_track,
                artist=self.current_artist,
                album=self.current_album,
                scroll_offset=self.lyrics_scroll_offset,
            )
        )

    # ── spotify connection ──────────────────────────────────────────

    @work
    async def init_spotify(self) -> None:
        try:
            self.spotify_client = SpotifyClient()
            self.notify("Connected to Spotify")
        except Exception as e:
            self.notify(f"Spotify error: {e}")

    @work
    async def poll_playback(self) -> None:
        if not self.spotify_client:
            self._enter_offline_mode()
            return

        if self.offline_mode:
            self.refresh_display()
            return

        # load playlists once
        if not self.playlists_data:
            try:
                playlists = self.spotify_client.get_user_playlists()
                if playlists:
                    self.playlists_data = playlists[:MAX_PLAYLISTS]
                    self.refresh_display()
            except Exception:
                pass

        try:
            playback = self.spotify_client.get_current_playback()
            self.api_error_count = 0

            if playback and playback.get("item"):
                track = playback["item"]
                track_id = track.get("id", "")

                self.current_track = track.get("name", "Unknown")
                self.current_artist = ", ".join(
                    a["name"] for a in track.get("artists", [])
                )
                album_info = track.get("album", {})
                self.current_album = album_info.get("name", "Unknown")
                self.is_playing = playback.get("is_playing", False)
                self.track_progress_ms = playback.get("progress_ms", 0)
                self.track_duration_ms = track.get("duration_ms", 0)
                self.track_popularity = track.get("popularity", 0)
                self.track_explicit = track.get("explicit", False)
                self.track_release_date = album_info.get("release_date", "")

                if track_id != self.current_track_id:
                    logger.debug(f"Track changed: {self.current_track}")
                    self.current_track_id = track_id
                    self.fetch_lyrics()
                    self.add_track_to_history(track)

                    # update album art
                    images = album_info.get("images", [])
                    if images:
                        new_url = images[-1].get("url", "")
                        if new_url != self.album_art_url:
                            self.album_art_url = new_url
                            self.process_album_art()

                self.refresh_display()
            else:
                self.current_track = "No music playing"
                self.current_artist = ""
                self.current_album = ""
                self.is_playing = False
                self.track_progress_ms = 0
                self.track_duration_ms = 0
                self.refresh_display()

        except Exception as e:
            error_str = str(e).lower()
            if "429" in error_str or "rate" in error_str or "limit" in error_str:
                logger.warning(f"Rate limited: {e}")
                self._enter_offline_mode()
                return

            self.api_error_count += 1
            if self.api_error_count >= 3:
                logger.warning(f"Too many API errors, going offline: {e}")
                self._enter_offline_mode()
                return

            self.refresh_display()

    # ── offline mode ────────────────────────────────────────────────

    def _enter_offline_mode(self) -> None:
        if self.offline_mode:
            return

        self.offline_mode = True
        self.notify("Offline mode - API unavailable")

        self.playlists_data = list(DEMO_PLAYLISTS)
        demo = DEMO_CURRENT_TRACK
        self.current_track = demo["name"]
        self.current_artist = ", ".join(a["name"] for a in demo["artists"])
        self.current_album = demo["album"]["name"]
        self.is_playing = False
        self.track_progress_ms = 45000
        self.track_duration_ms = demo["duration_ms"]
        self.track_popularity = demo["popularity"]
        self.track_explicit = demo["explicit"]
        self.track_release_date = "----"

        self.current_lyrics = DEMO_LYRICS
        self.lyrics_source = "Demo"
        self.ai_prediction = "AI unavailable (offline)"
        self.album_art_ascii = DEFAULT_ART

        self.refresh_display()

    # ── album art ───────────────────────────────────────────────────

    @work
    async def process_album_art(self) -> None:
        img = download_album_art(self.album_art_url)
        if img:
            self.album_art_ascii = render_album_art(img)
        else:
            self.album_art_ascii = DEFAULT_ART
        self.refresh_display()

    # ── lyrics ──────────────────────────────────────────────────────

    @work
    async def fetch_lyrics(self) -> None:
        if not self.current_track or self.current_track == "No music playing":
            return

        self.lyrics_source = "Searching..."
        self.current_lyrics = "Searching for lyrics..."
        self.refresh_display()

        try:
            lyrics, source = self.lyrics_service.get_lyrics(
                self.current_artist, self.current_track
            )
            if lyrics:
                self.current_lyrics = lyrics
                self.lyrics_source = source
            else:
                self.current_lyrics = (
                    f"No lyrics found for:\n"
                    f"{self.current_track}\n"
                    f"by {self.current_artist}"
                )
                self.lyrics_source = "Not found"
        except Exception as e:
            self.current_lyrics = f"Error: {e}"
            self.lyrics_source = "Error"

        self.lyrics_scroll_offset = 0
        self.refresh_display()

    # ── AI / vibechain ──────────────────────────────────────────────

    def add_track_to_history(self, track_data: dict) -> None:
        if not track_data or not self.ai_enabled or not self.spotify_client:
            return

        try:
            audio_features = self.spotify_client.get_audio_features_with_fallback(
                track_data
            )
            if audio_features:
                features = TrackFeatures(
                    danceability=audio_features.get("danceability", 0.5),
                    energy=audio_features.get("energy", 0.5),
                    valence=audio_features.get("valence", 0.5),
                    tempo=audio_features.get("tempo", 120.0),
                    acousticness=audio_features.get("acousticness", 0.0),
                    instrumentalness=audio_features.get("instrumentalness", 0.0),
                    liveness=audio_features.get("liveness", 0.0),
                    speechiness=audio_features.get("speechiness", 0.0),
                )
                self.recent_tracks.append(features)
                if len(self.recent_tracks) > MAX_RECENT_TRACKS:
                    self.recent_tracks = self.recent_tracks[-MAX_RECENT_TRACKS:]
                self.update_ai_prediction()
        except Exception as e:
            logger.error(f"Failed to add track to history: {e}")

    @work
    async def update_ai_prediction(self) -> None:
        if not self.ai_enabled or not self.recent_tracks:
            return

        try:
            self.ai_prediction = "Analyzing..."
            self.refresh_display()

            prediction = await self.vibechain_client.predict_next_vibe(
                self.recent_tracks
            )
            if prediction:
                mood = (
                    "energetic"
                    if prediction.energy > 0.7
                    else "chill"
                    if prediction.energy < 0.3
                    else "balanced"
                )
                vibe = (
                    "happy"
                    if prediction.valence > 0.7
                    else "sad"
                    if prediction.valence < 0.3
                    else "neutral"
                )
                dance = "danceable" if prediction.danceability > 0.7 else "mellow"
                self.ai_prediction = (
                    f"AI: {mood}, {vibe}, {dance} "
                    f"({prediction.confidence:.0%})"
                )

                if self.current_playlist_tracks:
                    self.ai_recommendations = (
                        self.vibechain_client.find_matching_tracks(
                            prediction, self.current_playlist_tracks
                        )[:5]
                    )
            else:
                self.ai_prediction = "Learning your taste..."
        except Exception as e:
            logger.error(f"AI prediction failed: {e}")
            self.ai_prediction = "AI unavailable"

        self.refresh_display()

    # ── key handling ────────────────────────────────────────────────

    def on_key(self, event) -> None:  # noqa: C901
        key = event.key

        # vertical navigation
        if key in ("up", "k"):
            if self.viewing_tracks:
                if self.current_playlist_tracks:
                    self.track_cursor = (self.track_cursor - 1) % len(
                        self.current_playlist_tracks
                    )
            else:
                if self.playlists_data:
                    self.playlist_cursor = (self.playlist_cursor - 1) % len(
                        self.playlists_data
                    )
            self.refresh_display()
            event.prevent_default()

        elif key in ("down", "j"):
            if self.viewing_tracks:
                if self.current_playlist_tracks:
                    self.track_cursor = (self.track_cursor + 1) % len(
                        self.current_playlist_tracks
                    )
            else:
                if self.playlists_data:
                    self.playlist_cursor = (self.playlist_cursor + 1) % len(
                        self.playlists_data
                    )
            self.refresh_display()
            event.prevent_default()

        # select / enter
        elif key == "enter":
            if self.viewing_tracks:
                self._play_selected_track()
            else:
                self._view_playlist_tracks()
            event.prevent_default()

        # play entire playlist
        elif key == "P":
            if not self.viewing_tracks:
                self._play_selected_playlist()
            event.prevent_default()

        # back from tracks
        elif key in ("escape", "b"):
            if self.viewing_tracks:
                self.viewing_tracks = False
                self.track_cursor = 0
                self.refresh_display()
            event.prevent_default()

        # lyrics scrolling
        elif key == "left":
            if self.lyrics_scroll_offset > 0:
                self.lyrics_scroll_offset -= 1
                self.refresh_display()
            event.prevent_default()

        elif key == "right":
            lyric_lines = self.current_lyrics.split("\n") if self.current_lyrics else []
            max_scroll = max(0, len(lyric_lines) - 25)
            if self.lyrics_scroll_offset < max_scroll:
                self.lyrics_scroll_offset += 1
                self.refresh_display()
            event.prevent_default()

        elif key == "l":
            lyric_lines = self.current_lyrics.split("\n") if self.current_lyrics else []
            max_scroll = max(0, len(lyric_lines) - 25)
            if self.lyrics_scroll_offset < max_scroll:
                self.lyrics_scroll_offset += 1
            else:
                self.lyrics_scroll_offset = 0
            self.refresh_display()
            event.prevent_default()

    # ── actions (bound to keys via BINDINGS) ────────────────────────

    def action_toggle_playback(self) -> None:
        if not self.spotify_client:
            return
        try:
            if self.is_playing:
                self.spotify_client.pause_playback()
            else:
                self.spotify_client.resume_playback()
        except Exception as e:
            self.notify(f"Error: {e}")

    def action_next_track(self) -> None:
        if not self.spotify_client:
            return
        try:
            self.spotify_client.skip_to_next()
        except Exception as e:
            self.notify(f"Error: {e}")

    def action_prev_track(self) -> None:
        if not self.spotify_client:
            return
        try:
            self.spotify_client.skip_to_previous()
        except Exception as e:
            self.notify(f"Error: {e}")

    def action_smart_shuffle(self) -> None:
        if not self.ai_enabled or not self.spotify_client:
            self.notify("AI shuffle not available")
            return

        if not self.recent_tracks:
            self.notify("Need more listening history")
            return

        try:
            if self.ai_recommendations:
                rec = self.ai_recommendations[0]
                track_name = rec.get("name", "Unknown")
                uri = rec.get("uri")
                if uri:
                    self.spotify_client.sp.start_playback(uris=[uri])
                    self.notify(f"Smart shuffle: {track_name}")
                    self.ai_recommendations = self.ai_recommendations[1:]
                else:
                    self.notify("Could not play recommendation")
            else:
                self.update_ai_prediction()
                self.notify("AI analyzing... try again in a moment")
        except Exception as e:
            logger.error(f"Smart shuffle failed: {e}")
            self.notify("Shuffle error - skipping normally")
            try:
                self.spotify_client.skip_to_next()
            except Exception:
                pass

    # ── playlist / track helpers ────────────────────────────────────

    def _play_selected_playlist(self) -> None:
        if not self.spotify_client or not self.playlists_data:
            return

        if 0 <= self.playlist_cursor < len(self.playlists_data):
            pl = self.playlists_data[self.playlist_cursor]
            uri = pl.get("uri")
            name = pl.get("name", "Unknown")
            if uri:
                try:
                    self.spotify_client.sp.start_playback(context_uri=uri)
                    self.notify(f"Playing: {name}")
                except Exception as e:
                    self.notify(f"Error: {e}")

    @work
    async def _view_playlist_tracks(self) -> None:
        if (not self.spotify_client and not self.offline_mode) or not self.playlists_data:
            return

        if not (0 <= self.playlist_cursor < len(self.playlists_data)):
            return

        pl = self.playlists_data[self.playlist_cursor]
        pl_id = pl.get("id")
        pl_name = pl.get("name", "Unknown")

        if not pl_id:
            return

        if self.offline_mode:
            from config import DEMO_TRACKS

            self.current_playlist_tracks = DEMO_TRACKS.get(
                pl_id,
                [
                    {
                        "track": {
                            "name": "Demo Track",
                            "artists": [{"name": "Demo Artist"}],
                            "duration_ms": 180000,
                            "id": "demo",
                            "uri": "spotify:track:demo",
                        }
                    }
                ],
            )
        else:
            try:
                self.notify(f"Loading: {pl_name}...")
                tracks = self.spotify_client.get_playlist_tracks(pl_id)
                self.current_playlist_tracks = tracks
            except Exception as e:
                self.notify(f"Error: {e}")
                return

        self.viewing_tracks = True
        self.track_cursor = 0
        self.tracks_scroll_offset = 0
        self.refresh_display()

    def _play_selected_track(self) -> None:
        if not self.spotify_client or not self.current_playlist_tracks:
            return

        if not (0 <= self.track_cursor < len(self.current_playlist_tracks)):
            return

        track_item = self.current_playlist_tracks[self.track_cursor]
        track = track_item.get("track", {})
        name = track.get("name", "Unknown")

        if self.playlists_data and 0 <= self.playlist_cursor < len(self.playlists_data):
            pl_uri = self.playlists_data[self.playlist_cursor].get("uri")
            if pl_uri:
                try:
                    self.spotify_client.sp.start_playback(
                        context_uri=pl_uri,
                        offset={"position": self.track_cursor},
                    )
                    self.notify(f"Playing: {name}")
                except Exception as e:
                    self.notify(f"Error: {e}")
