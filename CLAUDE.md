# spotifytui - AI context

## what this is

Terminal UI for Spotify with three panels (player, playlists, lyrics). Uses Textual framework with CSS-based layout. Optional AI recommendations via VibeChain API.

## project structure

```
src/
├── main.py              # entry point + vibechain process management
├── app.py               # SpotifyTUI(App) - compose, key handling, data fetching
├── config.py            # all constants, env vars, demo data
├── album_art.py         # half-block character rendering
├── spotify_client.py    # spotipy wrapper (rate limiting, caching, fallbacks)
├── lyrics_service.py    # genius API with extensive metadata cleanup
├── vibechain_client.py  # async ML client (aiohttp)
├── feature_estimator.py # genre-based audio feature estimation
├── logging_config.py    # rotating file handler with app-only filter
├── spotifytui.tcss      # textual CSS layout
└── widgets/
    ├── player.py        # PlayerWidget(Static)
    ├── playlists.py     # PlaylistWidget(Static)
    └── lyrics.py        # LyricsWidget(Static)
```

## build & run

```bash
pip install -e .   # editable install
spotifytui         # run via entry point
python src/main.py # run directly
```

## key architecture decisions

- **widgets use Static + render methods**: each widget has a `render_*()` method that returns a markup string. the app calls `widget.update(widget.render_*(...))` to push state. this is simpler than full reactive widgets but effective.
- **CSS-based layout**: `spotifytui.tcss` handles panel sizing, borders, padding. no inline layout math.
- **vibechain is optional**: app works fine without it. AI features degrade gracefully.
- **offline mode**: auto-activates after 3 API errors or rate limiting. shows demo data.
- **album art**: uses unicode half-block characters (▀▄█) for 2x vertical resolution.
- **rate limiting**: spotify client enforces 500ms between requests + retry on 429.
- **lyrics cleanup**: aggressive regex filtering to strip genius metadata, translations, contributor info.

## env vars

- `SPOTIPY_CLIENT_ID`, `SPOTIPY_CLIENT_SECRET` (required)
- `SPOTIPY_REDIRECT_URI` (default: `http://127.0.0.1:8888/callback`)
- `GENIUS_ACCESS_TOKEN` (optional, for lyrics)
- `VIBECHAIN_API_URL` (default: `http://localhost:8080`)
- `VIBECHAIN_API_PATH` (default: `~/Documents/GitHub/playlistify-api`)

## known quirks

- spotify auth token cached at `~/.cache/spotifytui/.spotify_cache`
- genius lyrics scraping can break if genius changes their page structure
- vibechain startup blocks for up to 15 seconds waiting for npm server
- `feature_estimator.py` has hardcoded genre databases -- will drift over time
- textual CSS has limited customization compared to web CSS
