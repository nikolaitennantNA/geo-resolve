"""Google Address Validation provider.

Validates and standardizes addresses — returns corrected address + coords + postal code.
Best for cleaning up messy/partial addresses into standardized format.

Uses the same API key as Google Geocoding (GOOGLE_MAPS_API_KEY or GOOGLE_PLACES_API_KEY).

Pricing: $17/1K requests.
"""

import os

import requests

from geo_resolve.providers.base import GeoProvider, GeoResult


class GoogleValidationProvider(GeoProvider):
    name = "google_validation"
    default_rate_limit = 0.05  # 50ms

    BASE_URL = "https://addressvalidation.googleapis.com/v1:validateAddress"

    def __init__(self, api_key: str | None = None, **kwargs):
        self.api_key = (
            api_key
            or os.getenv("GOOGLE_PLACES_API_KEY")
            or os.getenv("GOOGLE_MAPS_API_KEY")
        )

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def geocode(self, address: str, **kwargs) -> GeoResult:
        country_code = kwargs.get("country_bias", "").upper() or None
        body: dict = {
            "address": {
                "addressLines": [address],
            }
        }
        if country_code:
            body["address"]["regionCode"] = country_code

        try:
            resp = requests.post(
                self.BASE_URL,
                json=body,
                params={"key": self.api_key},
                headers={"Content-Type": "application/json"},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"  [google_validation] request error: {e}")
            return GeoResult(provider=self.name)

        result = data.get("result")
        if not result:
            return GeoResult(provider=self.name)

        # Extract coords
        geocode = result.get("geocode", {})
        loc = geocode.get("location", {})
        lat = loc.get("latitude")
        lon = loc.get("longitude")

        # Extract formatted address
        validated = result.get("address", {})
        formatted = validated.get("formattedAddress", "")

        if lat is not None:
            return GeoResult(
                lat=lat, lon=lon,
                display_name=formatted,
                provider=self.name,
            )

        return GeoResult(provider=self.name)
