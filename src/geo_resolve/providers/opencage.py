"""OpenCage Geocoding provider. Free tier: 2,500 req/day."""

import os

import requests

from geo_resolve.providers.base import GeoProvider, GeoResult


class OpenCageProvider(GeoProvider):
    name = "opencage"
    default_rate_limit = 1.0  # Free tier: 1 req/sec

    BASE_URL = "https://api.opencagedata.com/geocode/v1/json"

    def __init__(self, api_key: str | None = None, **kwargs):
        self.api_key = api_key or os.getenv("OPENCAGE_API_KEY")

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def geocode(self, address: str, **kwargs) -> GeoResult:
        params: dict = {"q": address, "key": self.api_key, "limit": 1, "no_annotations": 1}
        cc = kwargs.get("country_bias")
        if cc:
            params["countrycode"] = cc

        try:
            resp = requests.get(self.BASE_URL, params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as e:
            print(f"  [opencage] request error: {e}")
            return GeoResult(provider=self.name)

        if data.get("results"):
            geo = data["results"][0]["geometry"]
            return GeoResult(
                lat=geo["lat"],
                lon=geo["lng"],
                display_name=data["results"][0].get("formatted", ""),
                provider=self.name,
            )

        return GeoResult(provider=self.name)
