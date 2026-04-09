"""
Lyrics service for fetching song lyrics from Genius using LyricsGenius
"""

import os
import logging
from typing import Optional, Tuple
import re
import time
import lyricsgenius

logger = logging.getLogger(__name__)

class LyricsService:
    """Service for fetching song lyrics using LyricsGenius."""
    
    def __init__(self):
        # Try to get Genius API token from environment
        genius_token = os.getenv('GENIUS_ACCESS_TOKEN')
        
        if genius_token:
            try:
                self.genius = lyricsgenius.Genius(genius_token)
                self.genius.verbose = False  # Reduce output
                self.genius.remove_section_headers = True  # Clean up lyrics
                self.genius.skip_non_songs = True
                self.genius.excluded_terms = ["(Remix)", "(Live)", "(Demo)", "(Instrumental)"]
                self.has_genius = True
            except Exception as e:
                logger.warning(f"Failed to initialize Genius with token: {e}")
                self.genius = None
                self.has_genius = False
        else:
            self.genius = None
            self.has_genius = False
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
    
    def _clean_text(self, text: str) -> str:
        """Clean artist name and song title for better API matching."""
        if not text:
            return ""
        
        # Remove common patterns that might interfere with search
        text = re.sub(r'\s*\(.*?\)\s*', '', text)  # Remove parentheses content
        text = re.sub(r'\s*\[.*?\]\s*', '', text)  # Remove brackets content
        text = re.sub(r'\s*-\s*.*?$', '', text)   # Remove " - something" at end
        text = re.sub(r'\s*feat\..*?$', '', text, flags=re.IGNORECASE)  # Remove "feat."
        text = re.sub(r'\s*ft\..*?$', '', text, flags=re.IGNORECASE)    # Remove "ft."
        text = re.sub(r'\s+', ' ', text)          # Normalize whitespace
        return text.strip()
    
    def _rate_limit(self):
        """Implement basic rate limiting."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def get_lyrics_from_genius(self, artist: str, title: str) -> Optional[str]:
        """
        Fetch lyrics from Genius using LyricsGenius (if available).
        """
        if not self.has_genius or not self.genius:
            return None
            
        try:
            self._rate_limit()
            
            # Clean the inputs
            clean_artist = self._clean_text(artist)
            clean_title = self._clean_text(title)
            
            if not clean_artist or not clean_title:
                return None
            
            
            # Search for the song
            song = self.genius.search_song(clean_title, clean_artist)
            
            if song and song.lyrics:
                lyrics = song.lyrics.strip()
                
                # Advanced cleanup of Genius-specific artifacts and metadata
                lines = lyrics.split('\n')
                cleaned_lines = []
                skip_mode = False
                
                for line in lines:
                    line = line.strip()
                    line_lower = line.lower()
                    
                    # Skip lines with Genius metadata and artifacts
                    skip_patterns = [
                        'embed', 'you might also like', 'see also', 'lyrics from',
                        'genius.com', 'songwriters', 'producers', 'contributors',
                        'translations', 'türkçe', 'kriolu', 'kabuverdianu', 'português',
                        'español', 'français', 'bahasa indonesia', 'العربية', 'deutsch',
                        'polski', 'ελληνικά', 'almost', 'years after', 'examines',
                        'on the surface', 'read more', 'get tickets', 'how to format',
                        'lyrics', 'annotation', 'contributors', 'transcription',
                        'verified', 'produced by', 'written by', 'released', 'album',
                        'featuring', 'tags', 'comments', 'meaning', 'terjemahan',
                        'tradução', 'traduction', 'übersetzung', 'vertaling'
                    ]
                    
                    # Skip lines that contain metadata patterns
                    if any(pattern in line_lower for pattern in skip_patterns):
                        continue
                    
                    # Skip lines that are mostly numbers (often contributor counts)
                    if line.isdigit() or (len(line) < 50 and any(char.isdigit() for char in line) and 'contributor' in line_lower):
                        continue
                    
                    # Skip lines that look like section headers in brackets/caps
                    if (line.startswith('[') and line.endswith(']')) or line.isupper() and len(line) > 10:
                        continue
                    
                    # Skip very long descriptive lines (likely Genius descriptions)
                    if len(line) > 200:
                        continue
                    
                    # Skip lines with URLs or web-related content
                    if any(web_term in line_lower for web_term in ['http', 'www', '.com', 'genius', 'website']):
                        continue
                    
                    # Keep lines that look like actual lyrics
                    if line and len(line) > 1:
                        cleaned_lines.append(line)
                
                if cleaned_lines:
                    # Final cleanup pass
                    final_lyrics = '\n'.join(cleaned_lines)
                    
                    # Remove any remaining Genius artifacts at the beginning
                    lines = final_lyrics.split('\n')
                    start_idx = 0
                    
                    # Skip header junk and find where actual lyrics start
                    for i, line in enumerate(lines):
                        line_clean = line.strip().lower()
                        # Look for typical song start patterns or skip obvious metadata
                        if (not any(skip_word in line_clean for skip_word in 
                               ['contributor', 'translation', 'lyrics', 'song', 'artist', 'album']) and
                            len(line.strip()) > 5 and
                            not line.strip().isdigit()):
                            start_idx = i
                            break
                    
                    # Clean up the final result
                    clean_lyrics = '\n'.join(lines[start_idx:])
                    
                    # Remove any trailing metadata
                    if len(clean_lyrics.strip()) > 50:  # Make sure we have substantial content
                        return clean_lyrics.strip()
                    else:
                        logger.warning(f"Lyrics too short after cleanup for {clean_artist} - {clean_title}")
                        return None
                else:
                    logger.warning(f"No usable lyrics content for {clean_artist} - {clean_title}")
                    return None
            else:
                logger.warning(f"No lyrics found for {clean_artist} - {clean_title}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching lyrics from Genius for {artist} - {title}: {e}")
            return None
    
    def get_demo_lyrics(self, artist: str, title: str) -> str:
        """
        Generate helpful demo content when no API access is available.
        """
        return f"""🎵 {title} 🎵
by {artist}

📝 To get real lyrics, you need a Genius API token:

1. Go to https://genius.com/api-clients
2. Create an account and generate an access token
3. Set the environment variable:
   export GENIUS_ACCESS_TOKEN="your_token_here"
4. Restart the application

🎤 With a Genius token, you'll get:
• Real lyrics for millions of songs
• High-quality, accurate transcriptions
• Fast and reliable access
• Clean formatting

For now, enjoy the music! 🎵"""
    
    def get_lyrics_fallback(self, artist: str, title: str) -> Optional[str]:
        """
        Try alternative searches if the first attempt fails.
        """
        # Try variations of the search
        variations = []
        
        # Try splitting artist if it contains multiple artists
        if ',' in artist:
            main_artist = artist.split(',')[0].strip()
            variations.append((main_artist, title))
        
        if '&' in artist:
            main_artist = artist.split('&')[0].strip()
            variations.append((main_artist, title))
        
        if 'feat.' in artist.lower():
            main_artist = artist.lower().split('feat.')[0].strip()
            variations.append((main_artist, title))
        
        if 'ft.' in artist.lower():
            main_artist = artist.lower().split('ft.')[0].strip()
            variations.append((main_artist, title))
        
        for var_artist, var_title in variations:
            lyrics = self.get_lyrics_from_genius(var_artist, var_title)
            if lyrics:
                return lyrics
        
        return None
    


    def get_lyrics(self, artist: str, title: str) -> Tuple[Optional[str], str]:
        """
        Get lyrics for a song. Returns (lyrics, source) tuple.
        
        Args:
            artist: Artist name
            title: Song title
            
        Returns:
            Tuple of (lyrics_text, source_name) or (None, error_message)
        """
        if not artist or not title:
            return None, "Missing artist or title"
        
        
        if self.has_genius:
            # Try the main search with Genius
            lyrics = self.get_lyrics_from_genius(artist, title)
            if lyrics:
                return lyrics, "Genius"
            
            # Try fallback variations
            lyrics = self.get_lyrics_fallback(artist, title)
            if lyrics:
                return lyrics, "Genius (fallback)"
            
            # If no lyrics found
            return None, f"Lyrics not found for '{title}' by {artist}"
        else:
            # No Genius access - provide setup instructions
            demo_lyrics = self.get_demo_lyrics(artist, title)
            return demo_lyrics, "Setup required"
    
    def format_lyrics_display(self, lyrics: str, max_width: int = 80) -> str:
        """
        Format lyrics for display in the TUI.
        
        Args:
            lyrics: Raw lyrics text
            max_width: Maximum width for line wrapping
            
        Returns:
            Formatted lyrics text
        """
        if not lyrics:
            return ""
        
        # Split into lines and clean up
        lines = lyrics.split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                formatted_lines.append("")  # Keep empty lines for spacing
                continue
            
            # If line is too long, we could wrap it, but lyrics usually have natural breaks
            # For now, just add the line as-is
            formatted_lines.append(line)
        
        return '\n'.join(formatted_lines)
