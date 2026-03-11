"""OpenStreetMap Nominatim geocoding provider (free, no API key)."""

import requests

from geo_resolve.providers.base import GeoProvider, GeoResult


class NominatimProvider(GeoProvider):
    name = "nominatim"
    default_rate_limit = 1.1  # Nominatim policy: max 1 req/sec

    BASE_URL = "https://nominatim.openstreetmap.org/search"

    def __init__(self, user_agent: str = "geo-resolve/0.1", **kwargs):
        self.user_agent = user_agent
        self.country_codes = kwargs.get("country_codes")

    def is_configured(self) -> bool:
        return True  # No API key needed

    def geocode(self, address: str, **kwargs) -> GeoResult:
        params: dict = {
            "q": address,
            "format": "json",
            "limit": 1,
        }
        cc = kwargs.get("country_bias") or self.country_codes
        if cc:
            params["countrycodes"] = cc

        try:
            resp = requests.get(
                self.BASE_URL,
                params=params,
                headers={"User-Agent": self.user_agent},
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            if data:
                return GeoResult(
                    lat=float(data[0]["lat"]),
                    lon=float(data[0]["lon"]),
                    display_name=data[0].get("display_name", ""),
                    provider=self.name,
                )
        except Exception as e:
            print(f"  [nominatim] error: {e}")

        return GeoResult(provider=self.name)
