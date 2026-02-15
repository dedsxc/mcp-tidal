"""TIDAL client using tidalapi for music streaming API access."""

import logging
import tempfile
import webbrowser
from pathlib import Path
from typing import Any, Callable

import tidalapi
from tidalapi.session import Session

from .config import TidalConfig

logger = logging.getLogger(__name__)


class BrowserSession(tidalapi.Session):
    """Extended tidalapi.Session that automatically opens the login URL in a browser."""

    def login_oauth_simple(self, fn_print: Callable[[str], None] = logger.info) -> None:
        """Login to TIDAL with a remote link, automatically opening the URL in a browser.

        Args:
            fn_print: Function to display additional information

        Raises:
            TimeoutError: If the login takes too long
        """
        login, future = self.login_oauth()

        # Display information about the login
        text = f"Opening browser for TIDAL login. The code will expire in {login.expires_in} seconds"
        fn_print(text)

        # Open the URL in the default browser
        auth_url = login.verification_uri_complete
        if not auth_url.startswith("http"):
            auth_url = "https://" + auth_url
        webbrowser.open(auth_url)

        # Wait for the authentication to complete
        future.result()

    def login_session_file_auto(
        self,
        session_file: Path,
        do_pkce: bool = False,
        fn_print: Callable[[str], None] = logger.info,
    ) -> bool:
        """Logs in to the TIDAL api using an existing OAuth/PKCE session file,
        automatically opening the browser for authentication if needed.

        Args:
            session_file: The session json file
            do_pkce: Perform PKCE login. Default: Use OAuth logon
            fn_print: A function to display information

        Returns:
            True if the login was successful
        """
        self.load_session_from_file(session_file)

        # Session could not be loaded, attempt to create a new session
        if not self.check_login():
            if do_pkce:
                fn_print("Creating new session (PKCE)...")
                self.login_pkce(fn_print=fn_print)
            else:
                fn_print("Creating new session (OAuth)...")
                self.login_oauth_simple(fn_print=fn_print)

        if self.check_login():
            fn_print(f"TIDAL Login OK, creds saved in {session_file}")
            self.save_session_to_file(session_file)
            return True
        else:
            fn_print("TIDAL Login KO")
            return False


class TidalAPIError(Exception):
    """Base exception for TIDAL API errors."""

    def __init__(self, message: str, details: Any = None) -> None:
        super().__init__(message)
        self.details = details


class TidalAuthenticationError(TidalAPIError):
    """Authentication error."""


class TidalClient:
    """Client for TIDAL API using tidalapi."""

    def __init__(self, config: TidalConfig | None = None) -> None:
        """Initialize TIDAL client.

        Args:
            config: TIDAL API configuration (optional, uses defaults if not provided)
        """
        self.config = config or TidalConfig()
        self._session: BrowserSession | None = None
        
        # Use temp directory for session file
        token_path = tempfile.gettempdir() + "/tidal-session-oauth.json"
        self.session_file = Path(token_path)

    def _get_session(self) -> BrowserSession:
        """Get or create TIDAL session.

        Returns:
            Authenticated TIDAL session

        Raises:
            TidalAuthenticationError: If authentication fails
        """
        if self._session and self._session.check_login():
            return self._session

        # Create new session
        self._session = BrowserSession()
        
        # Try to authenticate
        if not self._session.login_session_file_auto(self.session_file):
            raise TidalAuthenticationError("Failed to authenticate with TIDAL")

        return self._session

    def check_auth(self) -> dict[str, Any]:
        """Check if there's an active authenticated session.

        Returns:
            Dictionary with authentication status and user info
        """
        if not self.session_file.exists():
            return {
                "authenticated": False,
                "message": "No session file found",
            }

        try:
            session = self._get_session()
            if session.check_login():
                user = session.user
                return {
                    "authenticated": True,
                    "message": "Valid TIDAL session",
                    "user": {
                        "id": user.id,
                        "username": getattr(user, "username", "N/A"),
                    },
                }
        except Exception as e:
            logger.error(f"Auth check failed: {e}")

        return {
            "authenticated": False,
            "message": "Invalid or expired session",
        }

    def login(self) -> dict[str, Any]:
        """Initiate TIDAL authentication process.

        Returns:
            Dictionary with authentication status
        """
        try:
            session = self._get_session()
            if session.check_login():
                return {
                    "status": "success",
                    "message": "Successfully authenticated with TIDAL",
                    "user_id": session.user.id,
                }
            else:
                return {
                    "status": "error",
                    "message": "Authentication failed",
                }
        except TimeoutError:
            return {
                "status": "error",
                "message": "Authentication timed out",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e),
            }

    def get_favorite_tracks(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get user's favorite tracks.

        Args:
            limit: Maximum number of tracks to retrieve

        Returns:
            List of track dictionaries

        Raises:
            TidalAuthenticationError: If not authenticated
        """
        session = self._get_session()
        favorites = session.user.favorites
        tracks = favorites.tracks(limit=limit)
        
        return [self._format_track(track) for track in tracks]

    def get_track_recommendations(self, track_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get recommended tracks based on a specific track.

        Args:
            track_id: TIDAL track ID
            limit: Maximum number of recommendations

        Returns:
            List of recommended track dictionaries

        Raises:
            TidalAuthenticationError: If not authenticated
        """
        session = self._get_session()
        track = session.track(track_id)
        
        if not track:
            raise TidalAPIError(f"Track with ID {track_id} not found")
        
        recommendations = track.get_track_radio(limit=limit)
        return [self._format_track(rec) for rec in recommendations]

    def create_playlist(
        self, title: str, description: str = "", track_ids: list[str] = None
    ) -> dict[str, Any]:
        """Create a new TIDAL playlist.

        Args:
            title: Playlist title
            description: Playlist description (optional)
            track_ids: List of track IDs to add (optional)

        Returns:
            Dictionary with playlist information

        Raises:
            TidalAuthenticationError: If not authenticated
        """
        session = self._get_session()
        playlist = session.user.create_playlist(title, description)
        
        if track_ids:
            playlist.add(track_ids)
        
        return {
            "id": playlist.id,
            "title": playlist.name,
            "description": playlist.description,
            "created": str(playlist.created) if hasattr(playlist, "created") else None,
            "last_updated": str(playlist.last_updated) if hasattr(playlist, "last_updated") else None,
            "track_count": playlist.num_tracks,
            "duration": playlist.duration,
            "url": f"https://tidal.com/playlist/{playlist.id}",
        }

    def get_user_playlists(self) -> list[dict[str, Any]]:
        """Get user's playlists.

        Returns:
            List of playlist dictionaries

        Raises:
            TidalAuthenticationError: If not authenticated
        """
        session = self._get_session()
        playlists = session.user.playlists()
        
        playlist_list = []
        for playlist in playlists:
            playlist_info = {
                "id": playlist.id,
                "title": playlist.name,
                "description": getattr(playlist, "description", ""),
                "created": str(playlist.created) if hasattr(playlist, "created") else None,
                "last_updated": str(playlist.last_updated) if hasattr(playlist, "last_updated") else None,
                "track_count": getattr(playlist, "num_tracks", 0),
                "duration": getattr(playlist, "duration", 0),
                "url": f"https://tidal.com/playlist/{playlist.id}",
            }
            playlist_list.append(playlist_info)
        
        # Sort by last_updated
        return sorted(
            playlist_list,
            key=lambda x: x.get("last_updated", ""),
            reverse=True,
        )

    def get_playlist_tracks(self, playlist_id: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get tracks from a specific playlist.

        Args:
            playlist_id: TIDAL playlist ID
            limit: Maximum number of tracks

        Returns:
            List of track dictionaries

        Raises:
            TidalAuthenticationError: If not authenticated
        """
        session = self._get_session()
        playlist = session.playlist(playlist_id)
        
        if not playlist:
            raise TidalAPIError(f"Playlist with ID {playlist_id} not found")
        
        tracks = playlist.items(limit=limit)
        return [self._format_track(track) for track in tracks]

    def delete_playlist(self, playlist_id: str) -> dict[str, str]:
        """Delete a TIDAL playlist.

        Args:
            playlist_id: TIDAL playlist ID

        Returns:
            Dictionary with deletion status

        Raises:
            TidalAuthenticationError: If not authenticated
        """
        session = self._get_session()
        playlist = session.playlist(playlist_id)
        
        if not playlist:
            raise TidalAPIError(f"Playlist with ID {playlist_id} not found")
        
        playlist.delete()
        
        return {
            "status": "success",
            "message": f"Playlist with ID {playlist_id} was successfully deleted",
        }

    def search(
        self,
        query: str,
        limit: int = 10,
        search_type: str = "tracks",
    ) -> dict[str, Any]:
        """Search for music on TIDAL.

        Args:
            query: Search query
            limit: Maximum number of results per type
            search_type: Type of search (tracks, albums, artists, playlists)

        Returns:
            Dictionary with search results

        Raises:
            TidalAuthenticationError: If not authenticated
        """
        session = self._get_session()
        
        # Map our search types to tidalapi types
        type_mapping = {
            "tracks": "tracks",
            "albums": "albums",
            "artists": "artists",
            "playlists": "playlists",
            "all": "all"
        }
        
        tidal_type = type_mapping.get(search_type, "tracks")
        
        results = {
            "query": query,
            "tracks": [],
            "albums": [],
            "artists": [],
            "playlists": [],
        }
        
        if tidal_type in ("tracks", "all"):
            search_results = session.search(query, models=[tidalapi.media.Track], limit=limit)
            if "tracks" in search_results and search_results["tracks"]:
                results["tracks"] = [self._format_track(track) for track in search_results["tracks"]]
        
        if tidal_type in ("albums", "all"):
            search_results = session.search(query, models=[tidalapi.media.Album], limit=limit)
            if "albums" in search_results and search_results["albums"]:
                results["albums"] = [self._format_album(album) for album in search_results["albums"]]
        
        if tidal_type in ("artists", "all"):
            search_results = session.search(query, models=[tidalapi.media.Artist], limit=limit)
            if "artists" in search_results and search_results["artists"]:
                results["artists"] = [self._format_artist(artist) for artist in search_results["artists"]]
        
        if tidal_type in ("playlists", "all"):
            search_results = session.search(query, models=[tidalapi.media.Playlist], limit=limit)
            if "playlists" in search_results and search_results["playlists"]:
                results["playlists"] = [self._format_playlist(playlist) for playlist in search_results["playlists"]]
        
        return results

    def get_track(self, track_id: str) -> dict[str, Any]:
        """Get track information.

        Args:
            track_id: TIDAL track ID

        Returns:
            Track dictionary

        Raises:
            TidalAuthenticationError: If not authenticated
        """
        session = self._get_session()
        track = session.track(track_id)
        
        if not track:
            raise TidalAPIError(f"Track with ID {track_id} not found")
        
        return self._format_track(track)

    def get_album(self, album_id: str) -> dict[str, Any]:
        """Get album information.

        Args:
            album_id: TIDAL album ID

        Returns:
            Album dictionary

        Raises:
            TidalAuthenticationError: If not authenticated
        """
        session = self._get_session()
        album = session.album(album_id)
        
        if not album:
            raise TidalAPIError(f"Album with ID {album_id} not found")
        
        return self._format_album(album)

    def get_artist(self, artist_id: str) -> dict[str, Any]:
        """Get artist information.

        Args:
            artist_id: TIDAL artist ID

        Returns:
            Artist dictionary

        Raises:
            TidalAuthenticationError: If not authenticated
        """
        session = self._get_session()
        artist = session.artist(artist_id)
        
        if not artist:
            raise TidalAPIError(f"Artist with ID {artist_id} not found")
        
        return self._format_artist(artist)

    def _format_track(self, track: Any) -> dict[str, Any]:
        """Format track object to dictionary."""
        return {
            "id": str(track.id),
            "title": track.name,
            "artist": track.artist.name if track.artist else "Unknown",
            "artist_id": str(track.artist.id) if track.artist else None,
            "album": track.album.name if track.album else "Unknown",
            "album_id": str(track.album.id) if track.album else None,
            "duration": track.duration,
            "url": f"https://tidal.com/track/{track.id}",
            "explicit": getattr(track, "explicit", False),
            "track_number": getattr(track, "track_num", None),
        }

    def _format_album(self, album: Any) -> dict[str, Any]:
        """Format album object to dictionary."""
        return {
            "id": str(album.id),
            "title": album.name,
            "artist": album.artist.name if album.artist else "Unknown",
            "artist_id": str(album.artist.id) if album.artist else None,
            "duration": getattr(album, "duration", None),
            "num_tracks": getattr(album, "num_tracks", 0),
            "release_date": str(album.release_date) if hasattr(album, "release_date") else None,
            "url": f"https://tidal.com/album/{album.id}",
        }

    def _format_artist(self, artist: Any) -> dict[str, Any]:
        """Format artist object to dictionary."""
        return {
            "id": str(artist.id),
            "name": artist.name,
            "url": f"https://tidal.com/artist/{artist.id}",
        }

    def _format_playlist(self, playlist: Any) -> dict[str, Any]:
        """Format playlist object to dictionary."""
        return {
            "id": str(playlist.id),
            "title": playlist.name,
            "description": getattr(playlist, "description", ""),
            "num_tracks": getattr(playlist, "num_tracks", 0),
            "duration": getattr(playlist, "duration", 0),
            "url": f"https://tidal.com/playlist/{playlist.id}",
        }
