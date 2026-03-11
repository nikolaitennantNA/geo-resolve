from geo_resolve.providers.base import GeoProvider
from geo_resolve.providers.google import GoogleProvider
from geo_resolve.providers.nominatim import NominatimProvider

PROVIDERS: dict[str, type[GeoProvider]] = {
    "google": GoogleProvider,
    "nominatim": NominatimProvider,
}

__all__ = ["GeoProvider", "GoogleProvider", "NominatimProvider", "PROVIDERS"]
