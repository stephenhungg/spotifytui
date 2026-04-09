"""
Album art rendering using half-block characters for high-resolution ASCII art.
"""

import io
import logging
from typing import Optional

import requests
from PIL import Image

from config import ALBUM_ART_WIDTH, ALBUM_ART_SAMPLE_SIZE

logger = logging.getLogger(__name__)

# half-block characters give us 2x vertical resolution
# upper half block: top pixel light, bottom pixel dark -> ▀
# lower half block: top pixel dark, bottom pixel light -> ▄
# full block: both dark -> █
# space: both light -> ' '
UPPER_HALF = "\u2580"  # ▀
LOWER_HALF = "\u2584"  # ▄
FULL_BLOCK = "\u2588"  # █

# brightness to shade mapping (5 levels per pixel)
SHADE_CHARS = [" ", "\u2591", "\u2592", "\u2593", "\u2588"]  # ░▒▓█


def render_album_art(img: Image.Image, width: int = ALBUM_ART_WIDTH) -> str:
    """Convert a PIL image to ASCII art using half-block characters.

    Each terminal character represents a 2-pixel-tall column, giving us
    double the vertical resolution compared to simple block characters.

    Args:
        img: PIL Image to render.
        width: number of character columns (each char is 2 terminal chars wide).

    Returns:
        Multi-line string of the rendered art.
    """
    height = width  # square aspect ratio

    # resample to target resolution
    img_resized = img.resize((width, height * 2), Image.LANCZOS)

    if img_resized.mode != "RGB":
        img_resized = img_resized.convert("RGB")

    pixels = img_resized.load()
    lines: list[str] = []

    for y in range(0, height * 2, 2):
        line = ""
        for x in range(width):
            # top and bottom pixel of this cell
            r_top, g_top, b_top = pixels[x, y]
            r_bot, g_bot, b_bot = pixels[x, min(y + 1, height * 2 - 1)]

            # luminance
            lum_top = int(0.299 * r_top + 0.587 * g_top + 0.114 * b_top)
            lum_bot = int(0.299 * r_bot + 0.587 * g_bot + 0.114 * b_bot)

            # threshold: above 128 = light, below = dark
            top_dark = lum_top < 128
            bot_dark = lum_bot < 128

            if top_dark and bot_dark:
                line += FULL_BLOCK + FULL_BLOCK
            elif top_dark and not bot_dark:
                line += UPPER_HALF + UPPER_HALF
            elif not top_dark and bot_dark:
                line += LOWER_HALF + LOWER_HALF
            else:
                line += "  "

        lines.append(line)

    return "\n".join(lines)


def download_album_art(url: str) -> Optional[Image.Image]:
    """Download album art from a URL.

    Args:
        url: image URL from Spotify API.

    Returns:
        PIL Image or None on failure.
    """
    if not url:
        return None

    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return Image.open(io.BytesIO(response.content))
    except Exception as e:
        logger.debug(f"Failed to download album art: {e}")

    return None


DEFAULT_ART = "\n".join(
    [
        "                                ",
        "     ██████████████████████     ",
        "     ██                  ██     ",
        "     ██    ██      ██    ██     ",
        "     ██    ██      ██    ██     ",
        "     ██    ██████████    ██     ",
        "     ██    ██      ██    ██     ",
        "     ██    ██      ██    ██     ",
        "     ██                  ██     ",
        "     ██    ▄▄▄▄▄▄▄▄▄▄    ██     ",
        "     ██    ██████████    ██     ",
        "     ██    ██████████    ██     ",
        "     ██                  ██     ",
        "     ██████████████████████     ",
        "                                ",
        "                                ",
    ]
)
