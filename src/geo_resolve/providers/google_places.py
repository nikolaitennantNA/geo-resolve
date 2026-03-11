"""Google Places Text Search (New) provider.

Finds actual business listings — returns coords + formatted address + business name.
More accurate than plain geocoding for named locations, but more expensive.

Uses the same API key as Google Geocoding (GOOGLE_MAPS_API_KEY or GOOGLE_PLACES_API_KEY).

Pricing: $32/1K requests (or $6.50/1K for Basic SKU if only requesting
location + formatted address, which is what we do).
"""

import os

import requests

from geo_resolve.providers.base import GeoProvider, GeoResult


class GooglePlacesProvider(GeoProvider):
    name = "google_places"
    default_rate_limit = 0.05  # 50ms — 50 QPS

    BASE_URL = "https://places.googleapis.com/v1/places:searchText"

    def __init__(self, api_key: str | None = None, **kwargs):
        self.api_key = (
            api_key
            or os.getenv("GOOGLE_PLACES_API_KEY")
            or os.getenv("GOOGLE_MAPS_API_KEY")
        )

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def geocode(self, address: str, **kwargs) -> GeoResult:
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location",
        }
        body: dict = {"textQuery": address, "maxResultCount": 1}

        try:
            resp = requests.post(self.BASE_URL, headers=headers, json=body, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"  [google_places] request error: {e}")
            return GeoResult(provider=self.name)

        places = data.get("places", [])
        if places:
            place = places[0]
            loc = place.get("location", {})
            return GeoResult(
                lat=loc.get("latitude"),
                lon=loc.get("longitude"),
                display_name=place.get("formattedAddress", ""),
                provider=self.name,
            )

        return GeoResult(provider=self.name)
