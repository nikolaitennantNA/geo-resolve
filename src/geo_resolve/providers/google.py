"""Google Maps Geocoding API provider."""

import os

import requests

from geo_resolve.providers.base import GeoProvider, GeoResult


class GoogleProvider(GeoProvider):
    name = "google"
    default_rate_limit = 0.05  # 50ms — Google allows 50 QPS

    BASE_URL = "https://maps.googleapis.com/maps/api/geocode/json"

    def __init__(self, api_key: str | None = None, **kwargs):
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_PLACES_API_KEY")
        self.region = kwargs.get("region")
        self.language = kwargs.get("language")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def geocode(self, address: str, **kwargs) -> GeoResult:
        params: dict = {"address": address, "key": self.api_key}
        if kwargs.get("country_bias") or self.region:
            params["region"] = kwargs.get("country_bias") or self.region
        if self.language:
            params["language"] = self.language

        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"  [google] request error: {e}")
            return GeoResult(provider=self.name)

        if data.get("status") == "OK" and data.get("results"):
            loc = data["results"][0]["geometry"]["location"]
            return GeoResult(
                lat=loc["lat"],
                lon=loc["lng"],
                display_name=data["results"][0].get("formatted_address", ""),
                provider=self.name,
            )

        return GeoResult(provider=self.name)
