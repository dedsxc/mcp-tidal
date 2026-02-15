"""Configuration management for MCP Tidal server."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class TidalConfig(BaseSettings):
    """TIDAL API configuration."""
    # API configuration
    base_url: str = Field(
        default="https://openapi.tidal.com",
        description="TIDAL API base URL",
    )
    auth_url: str = Field(
        default="https://auth.tidal.com/v1/oauth2/token",
        description="TIDAL OAuth2 token endpoint",
    )
    api_version: str = Field(
        default="v1",
        description="TIDAL API version",
    )
    country_code: str = Field(
        default="US",
        description="Country code for content availability (US, FR, GB, etc.)",
    )

    # HTTP client configuration
    timeout: int = Field(
        default=30,
        description="HTTP request timeout in seconds",
        ge=1,
        le=300,
    )
    max_retries: int = Field(
        default=3,
        description="Maximum number of retry attempts",
        ge=0,
        le=10,
    )
    rate_limit_per_minute: int = Field(
        default=100,
        description="Maximum requests per minute",
        ge=1,
        le=1000,
    )

    @property
    def api_base_url(self) -> str:
        """Full API base URL with version."""
        return f"{self.base_url}/{self.api_version}"
