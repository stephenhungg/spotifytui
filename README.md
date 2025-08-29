# spotifytui 🎵

just a clean spotify TUI that actually works!

check out vibechain-api for the machine learning part of this project: [vibechain-api](https://github.com/stephenhungg/vibechain-api)

## what it does

- plays your music 🎵
- shows your playlists 📚  
- displays lyrics 📝
- track info that's actually useful 📊
- clean three-panel layout
- doesn't break every 5 minutes

## setup (it's easy)

**1. get spotify credentials**
- hit up [spotify developer dashboard](https://developer.spotify.com/dashboard)
- make an app, get your client id & secret
- set redirect uri to: `http://127.0.0.1:8888/callback`

**2. install this thing**
```bash
git clone https://github.com/stephenhungg/spotifytui/
cd spotifytui
pipx install .
```

**3. set up your api keys**
```bash
# copy the template and add your keys
cp .env.example .env

# edit .env with your actual credentials
# SPOTIPY_CLIENT_ID=your_actual_client_id
# SPOTIPY_CLIENT_SECRET=your_actual_client_secret
# GENIUS_ACCESS_TOKEN=your_genius_token  # optional for lyrics
```

**4. run it**
```bash
spotifytui
```

that's it.

## controls

| key | what it does |
|-----|-------------|
| `space` | play/pause |
| `n` / `p` | next/previous track |
| `↑` / `↓` | navigate playlists/tracks |
| `j` / `k` | same but vim style |
| `←` / `→` | scroll lyrics |
| `enter` | play selected track/playlist |
| `shift+p` | play entire playlist |
| `q` | quit |

## features

**playback section:**
- current track info
- album art (16x16 pixel art cause why not)
- progress bar
- track stats (release year, popularity, etc.)

**playlists section:**
- all your spotify playlists
- browse tracks in any playlist
- play individual tracks or whole playlists

**lyrics section:**
- real lyrics from genius api
- clean formatting (strips out the garbage)

## lyrics setup (optional)

if you want actual lyrics instead of placeholder text:

1. get a genius api token from [genius.com/api-clients](https://genius.com/api-clients)
2. add it to your `.env` file: `GENIUS_ACCESS_TOKEN=your_token`
3. restart the app
4. lyrics will just work

## requirements

- spotify premium (api limitations unfortunately)
- python 3.8+
- working terminal

## dependencies

- `textual` - for the TUI magic
- `spotipy` - spotify api wrapper  
- `lyricsgenius` - lyrics from genius
- `pillow` - album art processing
- `requests` - http stuff
- `python-dotenv` - env file support

## troubleshooting

**"command not found"**: make sure pipx is in your PATH

**auth keeps failing**: double-check your redirect URI is exactly `http://127.0.0.1:8888/callback`

**no lyrics**: either set up genius token or just vibe with the placeholder

**nothing playing**: make sure spotify is actually running somewhere

**looks broken**: your terminal probably doesn't support unicode properly

## architecture

```
src/
├── simple_tui.py      # main app
├── spotify_client.py  # spotify api stuff  
└── lyrics_service.py  # genius api stuff
```

## contributing

sure, send a PR. keep it simple though.

---

*made for performative neovim users*
