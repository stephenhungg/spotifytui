#!/usr/bin/env python3
"""
Setup script for Spotify TUI
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="spotifytui",
    version="1.0.0",
    author="Stephen Hung",
    author_email="stephenhung@berkeley.edu",
    description="A beautiful Terminal User Interface for Spotify",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stephenhungg/spotifytui",
    py_modules=["simple_tui", "spotify_client", "lyrics_service"],
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Multimedia :: Sound/Audio :: Players",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
        "Environment :: Console :: Curses",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "spotifytui=simple_tui:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.css", "*.txt"],
    },
    keywords="spotify, tui, terminal, music, player, cli",
    project_urls={
        "Bug Reports": "https://github.com/stephenhungg/spotifytui/issues",
        "Source": "https://github.com/stephenhungg/spotifytui",
        "Documentation": "https://github.com/stephenhungg/spotifytui#readme",
    },
)




