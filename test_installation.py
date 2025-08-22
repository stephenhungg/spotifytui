#!/usr/bin/env python3
"""
Test script to verify Spotify TUI installation
"""

import sys
import importlib

def test_imports():
    """Test that all required packages can be imported."""
    required_packages = [
        'textual',
        'spotipy',
        'requests',
        'rich'
    ]
    
    print("Testing package imports...")
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package} - OK")
        except ImportError as e:
            print(f"❌ {package} - FAILED: {e}")
            return False
    
    return True

def test_spotify_client():
    """Test Spotify client initialization (without credentials)."""
    try:
        from src.spotify_client import SpotifyClient
        print("✅ SpotifyClient class - OK")
        return True
    except Exception as e:
        print(f"❌ SpotifyClient class - FAILED: {e}")
        return False

def test_screens():
    """Test screen components import."""
    try:
        from src.screens import (
            PlayerScreen,
            PlaylistsScreen,
            SearchScreen,
            ArtistScreen,
            AlbumScreen,
            LyricsScreen
        )
        print("✅ Screen components - OK")
        return True
    except Exception as e:
        print(f"❌ Screen components - FAILED: {e}")
        return False

def test_main_app():
    """Test main application import."""
    try:
        from src.app import SpotifyTUI
        print("✅ Main application - OK")
        return True
    except Exception as e:
        print(f"❌ Main application - FAILED: {e}")
        return False

def main():
    """Run all tests."""
    print("Spotify TUI Installation Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_spotify_client,
        test_screens,
        test_main_app
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your installation is ready.")
        print("\nNext steps:")
        print("1. Set up your Spotify API credentials")
        print("2. Copy env_example.txt to .env and fill in your details")
        print("3. Run: python main.py")
    else:
        print("❌ Some tests failed. Please check the errors above.")
        print("\nTroubleshooting:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Check Python version (requires 3.8+)")
        print("3. Verify all files are in the correct locations")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)




