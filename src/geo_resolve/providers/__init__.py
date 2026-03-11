from geo_resolve.providers.base import GeoProvider
from geo_resolve.providers.google import GoogleProvider
from geo_resolve.providers.locationiq import LocationIQProvider
from geo_resolve.providers.nominatim import NominatimProvider
from geo_resolve.providers.opencage import OpenCageProvider

PROVIDERS: dict[str, type[GeoProvider]] = {
    "google": GoogleProvider,
    "nominatim": NominatimProvider,
    "opencage": OpenCageProvider,
    "locationiq": LocationIQProvider,
}

__all__ = ["GeoProvider", "GoogleProvider", "NominatimProvider", "OpenCageProvider", "LocationIQProvider", "PROVIDERS"]
