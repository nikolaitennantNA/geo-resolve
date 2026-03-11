# geo-resolve

Provider-agnostic geocoding with persistent cache, rate limiting, and batch support.

## Install

```bash
pip install git+https://github.com/nikolaitennantNA/geo-resolve
# or with pandas support
pip install "geo-resolve[pandas] @ git+https://github.com/nikolaitennantNA/geo-resolve"
```

## Quick start

```python
from geo_resolve import Geocoder

gc = Geocoder()  # auto-selects provider from env vars
lat, lon = gc.geocode("Jl. Pemuda No.62, Semarang, Indonesia")

# Explicit provider
gc = Geocoder(provider="google", country_bias="id")
gc = Geocoder(provider="nominatim")
```

## Batch geocoding

```python
# CSV file → CSV file (with incremental saves)
gc = Geocoder(country_bias="id")
gc.geocode_csv("input.csv", "output.csv", address_col="address")

# pandas DataFrame
df = gc.geocode_df(df, address_col="address", lat_col="latitude", lon_col="longitude")
```

## CLI

```bash
geo-resolve input.csv output.csv
geo-resolve input.csv output.csv --provider google --country id
geo-resolve input.csv output.csv --address-col addr --lat-col lat --lon-col lng
```

## Providers

| Provider | API key env var | Cost | Rate limit | Best for |
|---|---|---|---|---|
| **Google Geocoding** | `GOOGLE_MAPS_API_KEY` | $5/1K requests (first $200/mo free) | 50 QPS | Street-level accuracy, global coverage |
| **Nominatim (OSM)** | None needed | Free | 1 req/sec | Bulk jobs where cost matters |

Auto-selection: Google if `GOOGLE_MAPS_API_KEY` is set, otherwise Nominatim.

## Persistent cache

All results are cached in SQLite at `~/.cache/geo-resolve/geocode.db`. Same address + provider combo is never re-requested — re-runs are instant.

```python
gc = Geocoder()
print(gc.cache_stats)  # {'total': 693, 'with_coords': 693, 'without_coords': 0}

# Disable cache
gc = Geocoder(cache=False)

# Custom cache location
gc = Geocoder(cache_path="/path/to/cache.db")
```

## Adding a provider

Subclass `GeoProvider` and register it:

```python
from geo_resolve.providers.base import GeoProvider, GeoResult

class MyProvider(GeoProvider):
    name = "my_provider"
    default_rate_limit = 0.5  # seconds between requests

    def is_configured(self) -> bool:
        return True

    def geocode(self, address: str, **kwargs) -> GeoResult:
        # Your geocoding logic here
        return GeoResult(lat=..., lon=..., provider=self.name)

# Use directly
gc = Geocoder(provider=MyProvider())
```

## Configuration

| Parameter | Default | Description |
|---|---|---|
| `provider` | Auto | `"google"`, `"nominatim"`, or a `GeoProvider` instance |
| `cache` | `True` | Enable persistent SQLite cache |
| `cache_path` | `~/.cache/geo-resolve/geocode.db` | Custom cache location |
| `country_bias` | `None` | ISO country code to bias results (e.g. `"id"` for Indonesia) |
| `rate_limit` | Provider default | Override seconds between requests |
| `verbose` | `True` | Print progress |
