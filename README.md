# geo-resolve

Provider-agnostic geocoding with persistent cache, rate limiting, and batch support.

Set the API key in your env, pass the provider name, done.

## Install

```bash
# Add to a project
uv add git+https://github.com/nikolaitennantNA/geo-resolve

# with pandas support
uv add "geo-resolve[pandas] @ git+https://github.com/nikolaitennantNA/geo-resolve"

# Or install directly
uv pip install git+https://github.com/nikolaitennantNA/geo-resolve
```

## Quick start

```python
from geo_resolve import Geocoder

# Just pass the provider name — it reads the API key from env automatically
gc = Geocoder(provider="google")
gc = Geocoder(provider="nominatim")    # free, no key needed
gc = Geocoder(provider="opencage")
gc = Geocoder(provider="locationiq")

# Or let it auto-select (picks first provider with a valid key)
gc = Geocoder()

lat, lon = gc.geocode("Jl. Pemuda No.62, Semarang, Indonesia")
# (-6.9739, 110.4203)

# Country bias for better results
gc = Geocoder(provider="google", country_bias="id")
```

## Providers

| Provider | Env var | Cost | Rate limit |
|---|---|---|---|
| `google` | `GOOGLE_MAPS_API_KEY` | $5/1K (first $200/mo free) | 50 QPS |
| `nominatim` | None needed | Free | 1/sec |
| `opencage` | `OPENCAGE_API_KEY` | Free tier: 2,500/day | 1/sec |
| `locationiq` | `LOCATIONIQ_API_KEY` | Free tier: 5,000/day | 2/sec |

Just set the env var and pass the name. That's it.

## Batch geocoding

```python
# CSV → CSV (incremental saves, resumable via cache)
gc = Geocoder(provider="google", country_bias="id")
gc.geocode_csv("input.csv", "output.csv", address_col="address")

# pandas DataFrame
df = gc.geocode_df(df, address_col="address", lat_col="latitude", lon_col="longitude")
```

## CLI

```bash
uv run geo-resolve input.csv output.csv
uv run geo-resolve input.csv output.csv -p google -c id
uv run geo-resolve input.csv output.csv --address-col addr --lat-col lat --lon-col lng
```

## Persistent cache

All results cached in SQLite at `~/.cache/geo-resolve/geocode.db`. Same address + provider is never re-requested. Re-runs are instant.

```python
gc.cache_stats  # {'total': 693, 'with_coords': 693, 'without_coords': 0}

Geocoder(cache=False)                        # disable
Geocoder(cache_path="/path/to/cache.db")     # custom location
```

## Adding a new provider

One file, ~40 lines. Subclass `GeoProvider`:

```python
from geo_resolve.providers.base import GeoProvider, GeoResult

class MyProvider(GeoProvider):
    name = "my_provider"
    default_rate_limit = 0.5

    def is_configured(self) -> bool:
        return bool(os.getenv("MY_PROVIDER_API_KEY"))

    def geocode(self, address: str, **kwargs) -> GeoResult:
        # Call your API, return GeoResult(lat=..., lon=..., provider=self.name)
        ...

# Use it
gc = Geocoder(provider=MyProvider())
```

Or add it to `providers/__init__.py` → `PROVIDERS` dict to use by name.

## All options

| Parameter | Default | Description |
|---|---|---|
| `provider` | Auto | `"google"`, `"nominatim"`, `"opencage"`, `"locationiq"`, or a `GeoProvider` instance |
| `cache` | `True` | Persistent SQLite cache |
| `cache_path` | `~/.cache/geo-resolve/geocode.db` | Custom cache path |
| `country_bias` | `None` | ISO country code (e.g. `"id"`, `"gb"`, `"us"`) |
| `rate_limit` | Provider default | Override seconds between requests |
| `verbose` | `True` | Print progress |
