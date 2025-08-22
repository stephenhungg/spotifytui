#!/usr/bin/env python3
"""
Spotify TUI Command Line Interface
Entry point for the spotifytui command
"""

import os
import sys

# Add the project directory to the Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_dir)

# Import and run the main app
from simple_tui import main as simple_main

def main():
    """Main entry point for the spotifytui command."""
    simple_main()

if __name__ == "__main__":
    main()
