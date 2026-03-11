"""Abstract base class for geocoding providers."""

from abc import ABC, abstractmethod


class GeoResult:
    """Result from a geocoding request."""

    __slots__ = ("lat", "lon", "display_name", "provider")

    def __init__(
        self,
        lat: float | None = None,
        lon: float | None = None,
        display_name: str = "",
        provider: str = "",
    ):
        self.lat = lat
        self.lon = lon
        self.display_name = display_name
        self.provider = provider

    @property
    def ok(self) -> bool:
        return self.lat is not None and self.lon is not None

    def __repr__(self) -> str:
        if self.ok:
            return f"GeoResult({self.lat:.6f}, {self.lon:.6f}, provider={self.provider!r})"
        return f"GeoResult(None, provider={self.provider!r})"


class GeoProvider(ABC):
    """Abstract geocoding provider."""

    name: str = "base"
    default_rate_limit: float = 1.0  # seconds between requests

    @abstractmethod
    def geocode(self, address: str, **kwargs) -> GeoResult:
        """Geocode a single address. Returns GeoResult."""
        ...

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if this provider has the required config (API keys etc)."""
        ...
