"""MCP server implementation for TIDAL API using FastMCP."""

import logging

from fastmcp import FastMCP

from .client import TidalClient, TidalAPIError, TidalAuthenticationError
from .config import TidalConfig

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp-tidal")

# Initialize FastMCP server
mcp = FastMCP("TIDAL Music")

# Global client instance
_client: TidalClient | None = None


def get_client() -> TidalClient:
    """Get or create TIDAL client instance."""
    global _client
    if _client is None:
        config = TidalConfig()
        _client = TidalClient(config)
    return _client


@mcp.tool()
def tidal_login() -> str:
    """Authenticate with TIDAL through browser login flow.
    
    This will open a browser window for you to log in to your TIDAL account.
    
    Returns:
        Authentication status message
    """
    try:
        client = get_client()
        result = client.login()
        
        if result.get("status") == "success":
            return f"✅ {result['message']}\nUser ID: {result.get('user_id')}"
        else:
            return f"❌ {result['message']}"
    except Exception as e:
        logger.exception("Error during login")
        return f"❌ Error: {str(e)}"


@mcp.tool()
def check_auth() -> str:
    """Check current TIDAL authentication status.
    
    Returns:
        Authentication status and user information
    """
    try:
        client = get_client()
        result = client.check_auth()
        
        if result.get("authenticated"):
            user = result.get("user", {})
            return f"✅ Authenticated with TIDAL\nUser ID: {user.get('id')}\nUsername: {user.get('username')}"
        else:
            return f"❌ Not authenticated: {result.get('message')}"
    except Exception as e:
        logger.exception("Error checking auth")
        return f"❌ Error: {str(e)}"


@mcp.tool()
def search_music(query: str, limit: int = 10) -> str:
    """Search for music content on TIDAL.

    Args:
        query: Search query string
        limit: Maximum results per type (default: 10)

    Returns:
        Formatted search results with IDs and URLs
    """
    try:
        client = get_client()
        results = client.search(query, limit=limit, search_type="all")
        
        output = [f"🔍 Search results for: {query}\n"]
        
        if results.get("tracks"):
            output.append(f"\n📻 TRACKS ({len(results['tracks'])}):")
            for track in results["tracks"][:10]:
                duration_min = track["duration"] // 60
                duration_sec = track["duration"] % 60
                output.append(
                    f"🎵 {track['title']}\n"
                    f"   Artist: {track['artist']}\n"
                    f"   Album: {track['album']}\n"
                    f"   Duration: {duration_min}:{duration_sec:02d}\n"
                    f"   URL: {track['url']}\n"
                    f"   ID: {track['id']}"
                )
        
        if results.get("albums"):
            output.append(f"\n\n💿 ALBUMS ({len(results['albums'])}):")
            for album in results["albums"][:10]:
                output.append(
                    f"💿 {album['title']}\n"
                    f"   Artist: {album['artist']}\n"
                    f"   Tracks: {album.get('num_tracks', 0)}\n"
                    f"   URL: {album['url']}\n"
                    f"   ID: {album['id']}"
                )
        
        if results.get("artists"):
            output.append(f"\n\n🎤 ARTISTS ({len(results['artists'])}):")
            for artist in results["artists"][:10]:
                output.append(
                    f"🎤 {artist['name']}\n"
                    f"   URL: {artist['url']}\n"
                    f"   ID: {artist['id']}"
                )
        
        if results.get("playlists"):
            output.append(f"\n\n📋 PLAYLISTS ({len(results['playlists'])}):")
            for playlist in results["playlists"][:10]:
                output.append(
                    f"📋 {playlist['title']}\n"
                    f"   Tracks: {playlist.get('num_tracks', 0)}\n"
                    f"   URL: {playlist['url']}\n"
                    f"   ID: {playlist['id']}"
                )
        
        if not any([results.get("tracks"), results.get("albums"), results.get("artists"), results.get("playlists")]):
            output.append("No results found.")
        
        return "\n".join(output)
    except TidalAuthenticationError:
        return "❌ Not authenticated. Please use tidal_login() first."
    except Exception as e:
        logger.exception("Error searching music")
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_track(track_id: str) -> str:
    """Get detailed information about a specific track.

    Args:
        track_id: TIDAL track ID

    Returns:
        Formatted track information with URL
    """
    try:
        client = get_client()
        track = client.get_track(track_id)
        
        duration_min = track["duration"] // 60
        duration_sec = track["duration"] % 60
        
        return (
            f"🎵 {track['title']}\n"
            f"   Artist: {track['artist']}\n"
            f"   Album: {track['album']}\n"
            f"   Duration: {duration_min}:{duration_sec:02d}\n"
            f"   Track #: {track.get('track_number', 'N/A')}\n"
            f"   Explicit: {'Yes' if track.get('explicit') else 'No'}\n"
            f"   URL: {track['url']}\n"
            f"   ID: {track['id']}"
        )
    except TidalAuthenticationError:
        return "❌ Not authenticated. Please use tidal_login() first."
    except Exception as e:
        logger.exception("Error getting track")
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_album(album_id: str) -> str:
    """Get detailed information about a specific album.

    Args:
        album_id: TIDAL album ID

    Returns:
        Formatted album information with URL
    """
    try:
        client = get_client()
        album = client.get_album(album_id)
        
        return (
            f"💿 {album['title']}\n"
            f"   Artist: {album['artist']}\n"
            f"   Tracks: {album.get('num_tracks', 0)}\n"
            f"   Release: {album.get('release_date', 'N/A')}\n"
            f"   URL: {album['url']}\n"
            f"   ID: {album['id']}"
        )
    except TidalAuthenticationError:
        return "❌ Not authenticated. Please use tidal_login() first."
    except Exception as e:
        logger.exception("Error getting album")
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_artist(artist_id: str) -> str:
    """Get detailed information about a specific artist.

    Args:
        artist_id: TIDAL artist ID

    Returns:
        Formatted artist information with URL
    """
    try:
        client = get_client()
        artist = client.get_artist(artist_id)
        
        return (
            f"🎤 {artist['name']}\n"
            f"   URL: {artist['url']}\n"
            f"   ID: {artist['id']}"
        )
    except TidalAuthenticationError:
        return "❌ Not authenticated. Please use tidal_login() first."
    except Exception as e:
        logger.exception("Error getting artist")
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_user_playlists() -> str:
    """Get the current user's playlists.
    
    Returns:
        List of user's playlists with URLs
    """
    try:
        client = get_client()
        playlists = client.get_user_playlists()
        
        if not playlists:
            return "📋 You don't have any playlists yet."
        
        output = [f"📋 Your playlists ({len(playlists)}):\n"]
        for playlist in playlists:
            output.append(
                f"📋 {playlist['title']}\n"
                f"   Description: {playlist.get('description', 'No description')}\n"
                f"   Tracks: {playlist.get('track_count', 0)}\n"
                f"   Last updated: {playlist.get('last_updated', 'N/A')}\n"
                f"   URL: {playlist['url']}\n"
                f"   ID: {playlist['id']}\n"
            )
        
        return "\n".join(output)
    except TidalAuthenticationError:
        return "❌ Not authenticated. Please use tidal_login() first."
    except Exception as e:
        logger.exception("Error getting playlists")
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_playlist_tracks(playlist_id: str, limit: int = 100) -> str:
    """Get all tracks from a specific playlist.

    Args:
        playlist_id: TIDAL playlist ID
        limit: Maximum number of tracks (default: 100)

    Returns:
        List of tracks from the playlist with URLs
    """
    try:
        client = get_client()
        tracks = client.get_playlist_tracks(playlist_id, limit)
        
        if not tracks:
            return f"📋 Playlist {playlist_id} is empty."
        
        output = [f"📋 Playlist tracks ({len(tracks)}):\n"]
        for i, track in enumerate(tracks, 1):
            duration_min = track["duration"] // 60
            duration_sec = track["duration"] % 60
            output.append(
                f"{i}. {track['title']} - {track['artist']} ({duration_min}:{duration_sec:02d})\n"
                f"   Album: {track['album']}\n"
                f"   URL: {track['url']}\n"
                f"   ID: {track['id']}\n"
            )
        
        return "\n".join(output)
    except TidalAuthenticationError:
        return "❌ Not authenticated. Please use tidal_login() first."
    except Exception as e:
        logger.exception("Error getting playlist tracks")
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_favorite_tracks(limit: int = 20) -> str:
    """Get the current user's favorite tracks.

    Args:
        limit: Maximum tracks to return (default: 20)

    Returns:
        User's favorite tracks with URLs
    """
    try:
        client = get_client()
        tracks = client.get_favorite_tracks(limit)
        
        if not tracks:
            return "⭐ You don't have any favorite tracks yet."
        
        output = [f"⭐ Your favorite tracks ({len(tracks)}):\n"]
        for i, track in enumerate(tracks, 1):
            duration_min = track["duration"] // 60
            duration_sec = track["duration"] % 60
            output.append(
                f"{i}. {track['title']} - {track['artist']} ({duration_min}:{duration_sec:02d})\n"
                f"   Album: {track['album']}\n"
                f"   URL: {track['url']}\n"
                f"   ID: {track['id']}\n"
            )
        
        return "\n".join(output)
    except TidalAuthenticationError:
        return "❌ Not authenticated. Please use tidal_login() first."
    except Exception as e:
        logger.exception("Error getting favorite tracks")
        return f"❌ Error: {str(e)}"


@mcp.tool()
def get_track_recommendations(track_id: str, limit: int = 20) -> str:
    """Get recommended tracks based on a specific track.

    Args:
        track_id: TIDAL track ID to base recommendations on
        limit: Maximum recommendations (default: 20)

    Returns:
        List of recommended tracks with URLs
    """
    try:
        client = get_client()
        tracks = client.get_track_recommendations(track_id, limit)
        
        if not tracks:
            return f"🎧 No recommendations found for track {track_id}."
        
        output = [f"🎧 Recommendations based on track {track_id} ({len(tracks)}):\n"]
        for i, track in enumerate(tracks, 1):
            duration_min = track["duration"] // 60
            duration_sec = track["duration"] % 60
            output.append(
                f"{i}. {track['title']} - {track['artist']} ({duration_min}:{duration_sec:02d})\n"
                f"   Album: {track['album']}\n"
                f"   URL: {track['url']}\n"
                f"   ID: {track['id']}\n"
            )
        
        return "\n".join(output)
    except TidalAuthenticationError:
        return "❌ Not authenticated. Please use tidal_login() first."
    except Exception as e:
        logger.exception("Error getting recommendations")
        return f"❌ Error: {str(e)}"


@mcp.tool()
def create_playlist(
    title: str,
    description: str = "",
    track_ids: list[str] | None = None,
) -> str:
    """Create a new playlist in the user's account.

    Args:
        title: Playlist title
        description: Playlist description (optional)
        track_ids: List of track IDs to add (optional)

    Returns:
        Created playlist information with URL
    """
    try:
        client = get_client()
        playlist = client.create_playlist(title, description, track_ids or [])
        
        return (
            f"✅ Playlist created successfully!\n"
            f"📋 {playlist['title']}\n"
            f"   Description: {playlist.get('description', 'No description')}\n"
            f"   Tracks: {playlist.get('track_count', 0)}\n"
            f"   URL: {playlist['url']}\n"
            f"   ID: {playlist['id']}"
        )
    except TidalAuthenticationError:
        return "❌ Not authenticated. Please use tidal_login() first."
    except Exception as e:
        logger.exception("Error creating playlist")
        return f"❌ Error: {str(e)}"


@mcp.tool()
def add_tracks_to_playlist(playlist_id: str, track_ids: list[str]) -> str:
    """Add tracks to an existing playlist.

    Args:
        playlist_id: Playlist ID to add tracks to
        track_ids: List of track IDs to add

    Returns:
        Confirmation message
    """
    try:
        client = get_client()
        result = client.add_tracks_to_playlist(playlist_id, track_ids)
        return f"✅ {result['message']}"
    except TidalAuthenticationError:
        return "❌ Not authenticated. Please use tidal_login() first."
    except Exception as e:
        logger.exception("Error adding tracks to playlist")
        return f"❌ Error: {str(e)}"


@mcp.tool()
def remove_tracks_from_playlist(playlist_id: str, track_indices: list[int]) -> str:
    """Remove tracks from an existing playlist.

    Args:
        playlist_id: Playlist ID to remove tracks from
        track_indices: List of track positions to remove (1-based, as shown in get_playlist_tracks)

    Returns:
        Confirmation message
    """
    try:
        client = get_client()
        result = client.remove_tracks_from_playlist(playlist_id, track_indices)
        return f"✅ {result['message']}"
    except TidalAuthenticationError:
        return "❌ Not authenticated. Please use tidal_login() first."
    except Exception as e:
        logger.exception("Error removing tracks from playlist")
        return f"❌ Error: {str(e)}"


@mcp.tool()
def delete_playlist(playlist_id: str) -> str:
    """Delete a playlist from the user's account.

    Args:
        playlist_id: Playlist ID to delete

    Returns:
        Confirmation message
    """
    try:
        client = get_client()
        result = client.delete_playlist(playlist_id)
        return f"✅ {result['message']}"
    except TidalAuthenticationError:
        return "❌ Not authenticated. Please use tidal_login() first."
    except Exception as e:
        logger.exception("Error deleting playlist")
        return f"❌ Error: {str(e)}"


def serve(transport: str = "stdio", host: str = "0.0.0.0", port: int = 8000):
    """Serve the MCP server.
    
    Args:
        transport: "stdio", "sse", or "streamable-http" (default: stdio)
        host: Host to bind (default: 0.0.0.0)
        port: Port to bind (default: 8000)
    """
    if transport in ("sse", "streamable-http"):
        logger.info(f"Starting MCP server in {transport.upper()} mode on {host}:{port}")
        mcp.run(transport=transport, host=host, port=port)
    else:
        logger.info("Starting MCP server in stdio mode")
        mcp.run()


def main():
    """Entry point for mcp-tidal command (stdio mode)."""
    serve(transport="stdio")


def main_sse():
    """Entry point for mcp-tidal-sse command (SSE mode on /sse)."""
    import os
    host = os.getenv("MCP_HOST", "0.0.0.0")
    port = int(os.getenv("MCP_PORT", "8000"))
    serve(transport="sse", host=host, port=port)


def main_http():
    """Entry point for mcp-tidal-http command (HTTP mode on /mcp)."""
    serve(transport="streamable-http", host="127.0.0.1", port=8000)

