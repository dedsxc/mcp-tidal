# MCP TIDAL Server 🎵

Model Context Protocol (MCP) server for TIDAL Music. Enables AI assistants (Claude, etc.) to access TIDAL catalog: search, playlists, favorites, and recommendations.

> **Note**: Uses [tidalapi](https://github.com/tamland/python-tidal) which accesses TIDAL's internal APIs (reverse-engineered).

## Installation

```bash
git clone https://github.com/yourusername/mcp-tidal.git
cd mcp-tidal
pip install -e .
```

## Configuration

### 1. Authentication

First time, authenticate with your TIDAL account:

```bash
python3 -c "from mcp_tidal.client import TidalClient; TidalClient().login()"
```

Session saved to `/tmp/tidal-session-oauth.json`.

### 2. Claude Desktop

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`  
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "tidal": {
      "command": "mcp-tidal"
    }
  }
}
```

## Available Tools

**Authentication**
- `tidal_login()` - Browser authentication
- `check_auth()` - Check status

**Search & Metadata**
- `search_music(query, limit)` - Search all content
- `get_track(track_id)` - Track details
- `get_album(album_id)` - Album details
- `get_artist(artist_id)` - Artist details

**Favorites & Recommendations**
- `get_favorite_tracks(limit)` - Your favorite tracks
- `get_track_recommendations(track_id, limit)` - Suggestions

**Playlists**
- `get_user_playlists()` - Your playlists
- `get_playlist_tracks(playlist_id, limit)` - Playlist tracks
- `create_playlist(title, description, track_ids)` - Create playlist
- `add_tracks_to_playlist(playlist_id, track_ids)` - Add tracks to playlist
- `remove_tracks_from_playlist(playlist_id, track_indices)` - Remove tracks from playlist
- `delete_playlist(playlist_id)` - Delete playlist

## Transport Modes

### stdio (default - for Claude Desktop)
```bash
mcp-tidal
```

### SSE (Server-Sent Events)
```bash
mcp-tidal-sse  # Runs on http://0.0.0.0:8000/sse
```

### HTTP Streamable
```bash
mcp-tidal-http  # Runs on http://127.0.0.1:8000/mcp
```
