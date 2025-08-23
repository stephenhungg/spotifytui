# 🎵 Setting up Genius Lyrics API

To get real lyrics in your Spotify TUI, you'll need to set up a free Genius API token.

## Quick Setup (5 minutes)

### 1. Get a Genius API Token
1. Go to [https://genius.com/api-clients](https://genius.com/api-clients)
2. Sign up or log in to your Genius account
3. Click "New API Client"
4. Fill out the form:
   - **App Name**: `SpotifyTUI` (or whatever you want)
   - **App Website URL**: `http://localhost` (just put anything)
5. Click "Save"
6. Copy your **Client Access Token**

### 2. Set the Environment Variable

**On macOS/Linux:**
```bash
# Add to your ~/.zshrc or ~/.bashrc file
export GENIUS_ACCESS_TOKEN="your_token_here"

# Or set it temporarily for this session
export GENIUS_ACCESS_TOKEN="your_token_here"
```

**On Windows:**
```cmd
set GENIUS_ACCESS_TOKEN=your_token_here
```

### 3. Restart SpotifyTUI
```bash
source .venv/bin/activate
spotifytui
```

## What You'll Get 🎤

- ✅ Real lyrics for millions of songs
- ✅ High-quality, accurate transcriptions  
- ✅ Fast and reliable access
- ✅ Clean formatting
- ✅ Search works with artist variations
- ✅ Copy/save lyrics functionality

## Troubleshooting

**Issue: "Setup required" still showing**
- Make sure you exported the environment variable correctly
- Restart your terminal session
- Check the token is set: `echo $GENIUS_ACCESS_TOKEN`

**Issue: No lyrics found for a song**
- Try the refresh button (🔄)
- Some songs might not be in the Genius database
- Check if the artist/song name is spelled correctly

That's it! Enjoy your lyrics! 🎵

