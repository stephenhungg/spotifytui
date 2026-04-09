"""
Lyrics panel widget.
"""

from textual.widgets import Static
from config import LYRICS_WINDOW_SIZE


class LyricsWidget(Static):
    """Renders the lyrics panel with scrolling."""

    def render_lyrics(
        self,
        lyrics: str,
        source: str,
        track: str,
        artist: str,
        album: str,
        scroll_offset: int,
    ) -> str:
        """Render the lyrics display with a scrollable viewport."""
        if not track or track == "No music playing":
            return (
                "[bold]LYRICS[/bold]\n\n"
                "[dim]No music playing[/dim]\n\n"
                "Start a song to see lyrics here."
            )

        lines_out = [
            f"[bold]LYRICS[/bold]  [dim]{source}[/dim]",
            "",
            f"[bold]{track}[/bold]",
            f"[dim]{artist}[/dim]",
            "",
            "─" * 48,
            "",
        ]

        if not lyrics:
            lines_out.append("[dim]Loading lyrics...[/dim]")
            return "\n".join(lines_out)

        lyric_lines = lyrics.split("\n")
        total = len(lyric_lines)
        window = LYRICS_WINDOW_SIZE

        max_scroll = max(0, total - window)
        offset = max(0, min(scroll_offset, max_scroll))

        start = offset
        end = min(start + window, total)

        visible = lyric_lines[start:end]
        lines_out.extend(visible)

        lines_out.append("")
        lines_out.append("─" * 48)

        if total > window:
            pct = (start + 1) / total * 100
            lines_out.append(f"[dim]{start + 1}-{end} of {total} ({pct:.0f}%) | left/right scroll[/dim]")
        else:
            lines_out.append("[dim]left/right to scroll[/dim]")

        return "\n".join(lines_out)
