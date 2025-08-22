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
    author="Your Name",
    author_email="your.email@example.com",
    description="A beautiful Terminal User Interface for Spotify",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/spotifytui",
    packages=find_packages(),
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
            "spotifytui=spotifytui_cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.css", "*.txt"],
    },
    keywords="spotify, tui, terminal, music, player, cli",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/spotifytui/issues",
        "Source": "https://github.com/yourusername/spotifytui",
        "Documentation": "https://github.com/yourusername/spotifytui#readme",
    },
)




