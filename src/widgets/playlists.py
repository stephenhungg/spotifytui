"""
Playlist and track list panel widget.
"""

from typing import Any

from textual.widgets import Static
from config import TRACKS_WINDOW_SIZE


class PlaylistWidget(Static):
    """Renders the playlist / track-list panel."""

    def render_playlists(
        self,
        playlists: list[dict[str, Any]],
        cursor: int,
        offline: bool,
    ) -> str:
        """Render the playlist list view."""
        if not playlists:
            return "PLAYLISTS\n\nNo playlists loaded"

        title = "PLAYLISTS (offline)" if offline else "PLAYLISTS"
        lines = [
            f"[bold]{title}[/bold]",
            "[dim]j/k navigate | enter view | P play[/dim]",
            "",
        ]

        for i, pl in enumerate(playlists):
            name = pl.get("name", "Unknown")
            total = pl.get("tracks", {}).get("total", 0)
            owner = pl.get("owner", {}).get("display_name", "")

            if i == cursor:
                lines.append(f"[bold green]> {name}[/bold green]")
                lines.append(f"  [dim green]{owner} - {total} tracks[/dim green]")
            else:
                lines.append(f"  {name}")
                lines.append(f"  [dim]{owner} - {total} tracks[/dim]")
            lines.append("")

        return "\n".join(lines)

    def render_tracks(
        self,
        tracks: list[dict[str, Any]],
        cursor: int,
        scroll_offset: int,
        playlist_name: str,
    ) -> str:
        """Render the track list view for a selected playlist."""
        if not tracks:
            return "TRACKS\n\nLoading..."

        total = len(tracks)
        window = TRACKS_WINDOW_SIZE

        # auto-scroll window
        if cursor < scroll_offset:
            scroll_offset = cursor
        elif cursor >= scroll_offset + window:
            scroll_offset = cursor - window + 1
        scroll_offset = max(0, min(scroll_offset, total - window))

        start = scroll_offset
        end = min(start + window, total)

        lines = [
            f"[bold]{playlist_name}[/bold]",
            f"[dim]{start + 1}-{end} of {total} | j/k nav | enter play | esc back[/dim]",
            "",
        ]

        for i in range(start, end):
            item = tracks[i]
            track = item.get("track", {})
            if not track:
                continue

            name = track.get("name", "Unknown")
            artists = ", ".join(a["name"] for a in track.get("artists", []))
            dur_ms = track.get("duration_ms", 0)
            dur_fmt = f"{dur_ms // 60000}:{(dur_ms % 60000) // 1000:02d}"

            num = i + 1
            if i == cursor:
                lines.append(f"[bold cyan]> {num:3d}. {name}[/bold cyan]")
                lines.append(f"       [dim cyan]{artists} - {dur_fmt}[/dim cyan]")
            else:
                lines.append(f"  {num:3d}. {name}")
                lines.append(f"       [dim]{artists} - {dur_fmt}[/dim]")
            lines.append("")

        if total > window:
            pct = (cursor + 1) / total * 100
            lines.append(f"[dim]{cursor + 1}/{total} ({pct:.0f}%)[/dim]")

        return "\n".join(lines)
