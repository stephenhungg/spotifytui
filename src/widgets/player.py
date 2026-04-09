"""
Player panel widget -- shows album art, track info, progress bar, and AI prediction.
"""

from textual.widgets import Static
from config import PROGRESS_BAR_WIDTH


class PlayerWidget(Static):
    """Renders the now-playing panel."""

    def render_player(
        self,
        track: str,
        artist: str,
        album: str,
        is_playing: bool,
        progress_ms: int,
        duration_ms: int,
        popularity: int,
        explicit: bool,
        release_date: str,
        album_art_ascii: str,
        ai_prediction: str,
        offline: bool,
    ) -> str:
        """Build the player display string.

        Called by the app whenever playback state changes.
        """
        if track == "No music playing":
            return (
                "SPOTIFY TUI\n\n"
                "No music playing\n\n"
                "Start playing in Spotify\n"
                "and it will appear here."
            )

        status = "PLAYING" if is_playing else "PAUSED"
        status_icon = ">" if is_playing else "||"

        # time
        prog_s = progress_ms // 1000
        dur_s = duration_ms // 1000
        prog_fmt = f"{prog_s // 60}:{prog_s % 60:02d}"
        dur_fmt = f"{dur_s // 60}:{dur_s % 60:02d}"

        # progress bar
        ratio = progress_ms / duration_ms if duration_ms > 0 else 0
        filled = int(ratio * PROGRESS_BAR_WIDTH)
        bar = "━" * filled + "╸" + "─" * (PROGRESS_BAR_WIDTH - filled - 1)

        # truncation helpers
        def trunc(s: str, n: int) -> str:
            return s if len(s) <= n else s[: n - 3] + "..."

        track_display = trunc(track, 44)
        artist_display = trunc(artist, 44)
        album_display = trunc(album, 44)

        explicit_tag = " [E]" if explicit else ""
        year = release_date[:4] if len(release_date) >= 4 else "----"

        # AI line
        ai_line = ai_prediction if ai_prediction else "Learning your taste..."

        mode_tag = " [OFFLINE]" if offline else ""

        lines = [
            f"[bold]{status} {status_icon}{mode_tag}[/bold]",
            "",
            album_art_ascii,
            "",
            f"[bold]{track_display}[/bold]{explicit_tag}",
            f"[dim]{artist_display}[/dim]",
            f"[dim]{album_display}[/dim]",
            "",
            f"  {prog_fmt}  {bar}  {dur_fmt}",
            "",
            f"[dim]{year}  |  popularity {popularity}/100[/dim]",
            "",
            f"[italic dim]{trunc(ai_line, 50)}[/italic dim]",
        ]

        return "\n".join(lines)
