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

## Docker

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN pip install -e .
CMD ["mcp-tidal-http"]
```

```bash
docker build -t mcp-tidal .

# 1. Authenticate locally first
python3 -c "from mcp_tidal.client import TidalClient; TidalClient().login()"

# 2. Run with session file mounted
docker run -v /tmp/tidal-session-oauth.json:/tmp/tidal-session-oauth.json \
           -p 8000:8000 mcp-tidal
```

**docker-compose.yml**:
```yaml
version: '3.8'
services:
  mcp-tidal:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - /tmp/tidal-session-oauth.json:/tmp/tidal-session-oauth.json:ro
    command: mcp-tidal-http
```
