#!/usr/bin/env python3
"""
Spotify TUI - A Terminal User Interface for Spotify
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.app import SpotifyTUI

def main():
    """Main entry point for the Spotify TUI application."""
    try:
        app = SpotifyTUI()
        app.run()
    except KeyboardInterrupt:
        print("\nGoodbye! 👋")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()




