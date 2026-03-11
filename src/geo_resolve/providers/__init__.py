from geo_resolve.providers.base import GeoProvider
from geo_resolve.providers.google import GoogleProvider
from geo_resolve.providers.google_places import GooglePlacesProvider
from geo_resolve.providers.google_validation import GoogleValidationProvider
from geo_resolve.providers.locationiq import LocationIQProvider
from geo_resolve.providers.nominatim import NominatimProvider
from geo_resolve.providers.opencage import OpenCageProvider

PROVIDERS: dict[str, type[GeoProvider]] = {
    "google": GoogleProvider,
    "google_places": GooglePlacesProvider,
    "google_validation": GoogleValidationProvider,
    "nominatim": NominatimProvider,
    "opencage": OpenCageProvider,
    "locationiq": LocationIQProvider,
}

__all__ = [
    "GeoProvider", "GoogleProvider", "GooglePlacesProvider",
    "GoogleValidationProvider", "NominatimProvider",
    "OpenCageProvider", "LocationIQProvider", "PROVIDERS",
]
