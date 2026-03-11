"""LocationIQ geocoding provider. Free tier: 5,000 req/day, 2 req/sec."""

import os

import requests

from geo_resolve.providers.base import GeoProvider, GeoResult


class LocationIQProvider(GeoProvider):
    name = "locationiq"
    default_rate_limit = 0.5  # Free tier: 2 req/sec

    BASE_URL = "https://us1.locationiq.com/v1/search"

    def __init__(self, api_key: str | None = None, **kwargs):
        self.api_key = api_key or os.getenv("LOCATIONIQ_API_KEY")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def geocode(self, address: str, **kwargs) -> GeoResult:
        params: dict = {"q": address, "key": self.api_key, "format": "json", "limit": 1}
        cc = kwargs.get("country_bias")
        if cc:
            params["countrycodes"] = cc

        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"  [locationiq] request error: {e}")
            return GeoResult(provider=self.name)

        if data:
            return GeoResult(
                lat=float(data[0]["lat"]),
                lon=float(data[0]["lon"]),
                display_name=data[0].get("display_name", ""),
                provider=self.name,
            )

        return GeoResult(provider=self.name)
