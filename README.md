# spotifytui

a terminal UI for spotify with lyrics and AI-powered recommendations.

check out [vibechain-api](https://github.com/stephenhungg/vibechain-api) for the machine learning backend.

three-panel layout: now playing + album art on the left, playlists in the middle, lyrics on the right. vim keybindings because obviously.

## setup

**1. spotify credentials**

go to [developer.spotify.com/dashboard](https://developer.spotify.com/dashboard), create an app, grab your client id + secret. set the redirect URI to `http://127.0.0.1:8888/callback`.

**2. install**

```bash
git clone https://github.com/stephenhungg/spotifytui
cd spotifytui
pip install .
```

or for development:

```bash
pip install -e .
```

**3. configure**

```bash
cp .env.example .env
# edit .env with your credentials
```

**4. run**

```bash
spotifytui
```

first run will open a browser for spotify OAuth. after that it's cached.

## controls

| key | action |
|-----|--------|
| `space` | play/pause |
| `n` / `p` | next / previous track |
| `s` | smart shuffle (AI-powered) |
| `j` / `k` or `up` / `down` | navigate playlists/tracks |
| `enter` | select playlist / play track |
| `P` (shift+p) | play entire playlist |
| `esc` / `b` | back to playlists |
| `left` / `right` | scroll lyrics |
| `l` | scroll lyrics (loops) |
| `q` | quit |

## features

**player panel**
- album art rendered as half-block ASCII (2x vertical resolution)
- track info, progress bar, release year, popularity
- AI vibe prediction from VibeChain

**playlist panel**
- browse your spotify playlists
- view and play individual tracks
- play entire playlists
- scrollable track list with cursor

**lyrics panel**
- real lyrics from Genius API
- auto-fetches on track change
- clean formatting (strips Genius metadata artifacts)
- scrollable viewport

**AI recommendations** (optional)
- VibeChain ML model analyzes your listening session
- predicts your next vibe (energy, mood, danceability)
- smart shuffle picks tracks matching the prediction
- falls back gracefully when unavailable

**offline mode**
- auto-activates when Spotify API is rate-limited
- demo interface so you can still explore the UI
- reconnects when API becomes available

## lyrics setup

optional but recommended. get a token from [genius.com/api-clients](https://genius.com/api-clients) and add to `.env`:

```
GENIUS_ACCESS_TOKEN=your_token
```

## AI setup

optional. requires [vibechain-api](https://github.com/stephenhungg/vibechain-api) running locally:

```bash
# in a separate terminal
cd /path/to/vibechain-api
npm run dev
```

or set the path in `.env`:

```
VIBECHAIN_API_PATH=/path/to/vibechain-api
VIBECHAIN_API_URL=http://localhost:8080
```

spotifytui will try to auto-start the API on launch.

## architecture

```
src/
├── main.py              # entry point, vibechain startup
├── app.py               # textual app, key handling, data fetching
├── config.py            # constants, env vars, demo data
├── album_art.py         # half-block ASCII art rendering
├── spotify_client.py    # spotipy wrapper with rate limiting
├── lyrics_service.py    # genius API with cleanup
├── vibechain_client.py  # ML recommendation client
├── feature_estimator.py # audio feature fallback estimation
├── logging_config.py    # structured logging setup
├── spotifytui.tcss      # textual CSS theme
└── widgets/
    ├── player.py        # now-playing panel
    ├── playlists.py     # playlist/track panel
    └── lyrics.py        # lyrics panel
```

## debugging

logs go to `spotifytui_debug.log` in the project root:

```bash
tail -f spotifytui_debug.log
# or
python log_viewer.py
python log_viewer.py --stats
```

## requirements

- python 3.10+
- spotify premium (API needs active playback)
- a terminal with unicode support

## dependencies

- [textual](https://textual.textualize.io/) - TUI framework
- [spotipy](https://spotipy.readthedocs.io/) - spotify API
- [lyricsgenius](https://lyricsgenius.readthedocs.io/) - genius lyrics
- [pillow](https://pillow.readthedocs.io/) - album art processing
- [aiohttp](https://docs.aiohttp.org/) - async HTTP for VibeChain
