"""Pydantic models for TIDAL API responses."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class TidalResource(BaseModel):
    """Base TIDAL resource following JSON:API spec."""

    id: str
    type: str
    attributes: dict[str, Any] = Field(default_factory=dict)
    relationships: dict[str, Any] = Field(default_factory=dict)


class Track(BaseModel):
    """TIDAL track model."""

    id: str
    title: str
    duration: int  # seconds
    isrc: str | None = None
    explicit: bool = False
    audio_quality: str | None = None
    artist_names: list[str] = Field(default_factory=list)
    album_title: str | None = None
    track_number: int | None = None
    volume_number: int | None = None
    release_date: str | None = None
    url: str | None = None


class Album(BaseModel):
    """TIDAL album model."""

    id: str
    title: str
    number_of_tracks: int = 0
    number_of_volumes: int = 1
    release_date: str | None = None
    duration: int = 0  # seconds
    explicit: bool = False
    upc: str | None = None
    artist_names: list[str] = Field(default_factory=list)
    cover_art_url: str | None = None
    url: str | None = None


class Artist(BaseModel):
    """TIDAL artist model."""

    id: str
    name: str
    picture_url: str | None = None
    bio: str | None = None
    url: str | None = None


class Playlist(BaseModel):
    """TIDAL playlist model."""

    id: str
    title: str
    description: str | None = None
    number_of_tracks: int = 0
    duration: int = 0  # seconds
    public: bool = True
    creator: str | None = None
    created_at: datetime | None = None
    last_modified_at: datetime | None = None
    cover_art_url: str | None = None
    url: str | None = None


class SearchResults(BaseModel):
    """TIDAL search results."""

    tracks: list[Track] = Field(default_factory=list)
    albums: list[Album] = Field(default_factory=list)
    artists: list[Artist] = Field(default_factory=list)
    playlists: list[Playlist] = Field(default_factory=list)
    top_hits: list[Track | Album | Artist] = Field(default_factory=list)
    total_tracks: int = 0
    total_albums: int = 0
    total_artists: int = 0
    total_playlists: int = 0


class UserCollection(BaseModel):
    """User's collection of favorited items."""

    id: str
    type: Literal["albums", "artists", "tracks", "videos", "playlists"]
    total_items: int = 0
    items: list[Track | Album | Artist | Playlist] = Field(default_factory=list)
