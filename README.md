# spotifytui 🎵

just a clean spotify TUI that actually works. no bullshit.

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
git clone <your-repo-url>
cd spotifytui
pipx install .
```

**3. set your env vars**
```bash
# add to your ~/.zshrc or ~/.bashrc
export SPOTIPY_CLIENT_ID="your_client_id"
export SPOTIPY_CLIENT_SECRET="your_client_secret" 
export SPOTIPY_REDIRECT_URI="http://127.0.0.1:8888/callback"
export GENIUS_ACCESS_TOKEN="your_genius_token"  # optional for lyrics
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
- auto-scrolling
- clean formatting (strips out the garbage)

## lyrics setup (optional)

if you want actual lyrics instead of placeholder text:

1. get a genius api token from [genius.com/api-clients](https://genius.com/api-clients)
2. add it to your env: `export GENIUS_ACCESS_TOKEN="your_token"`
3. restart your terminal
4. lyrics will just work

## requirements

- spotify premium (api limitations, not my fault)
- python 3.8+
- working terminal
- basic understanding of environment variables

## dependencies

the usual suspects:
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

simple and clean. no over-engineering.

## contributing

sure, send a PR. keep it simple though.

---

*made for people who like music and terminals. if you need a gui, this isn't for you.*