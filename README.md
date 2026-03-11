# geo-resolve

Provider-agnostic geocoding with persistent cache, rate limiting, and batch support.

Set the API key in your `.env`, pass the provider name, done.

## Install

```bash
uv add git+https://github.com/nikolaitennantNA/geo-resolve

# with pandas support
uv add "geo-resolve[pandas] @ git+https://github.com/nikolaitennantNA/geo-resolve"
```

## Quick start

```python
from geo_resolve import Geocoder

gc = Geocoder(provider="google")
lat, lon = gc.geocode("Jl. Pemuda No.62, Semarang, Indonesia")
# (-6.9739, 110.4203)
```

## Providers

All Google providers use the same key (`GOOGLE_MAPS_API_KEY` or `GOOGLE_PLACES_API_KEY`).

| Provider | Env var | Cost | Rate | What it does |
|---|---|---|---|---|
| `google` | `GOOGLE_MAPS_API_KEY` | $5/1K | 50 QPS | Address → coords (standard geocoding) |
| `google_places` | `GOOGLE_MAPS_API_KEY` | $32/1K | 50 QPS | Query → business listing + coords + address |
| `google_validation` | `GOOGLE_MAPS_API_KEY` | $17/1K | 50 QPS | Validates/corrects address + returns coords |
| `nominatim` | None | Free | 1/sec | OpenStreetMap geocoding, no key needed |
| `opencage` | `OPENCAGE_API_KEY` | Free: 2,500/day | 1/sec | Multi-source geocoding |
| `locationiq` | `LOCATIONIQ_API_KEY` | Free: 5,000/day | 2/sec | Nominatim-based with higher limits |

```python
gc = Geocoder(provider="google")              # address → coords
gc = Geocoder(provider="google_places")       # finds business by name
gc = Geocoder(provider="google_validation")   # cleans up messy addresses
gc = Geocoder(provider="nominatim")           # free, no key needed
gc = Geocoder(provider="opencage")
gc = Geocoder(provider="locationiq")

# Or let it auto-select (picks first provider with a valid key)
gc = Geocoder()
```

## Input / Output

### Python

```python
from geo_resolve import Geocoder

gc = Geocoder(provider="google", country_bias="id")

# Single address → (lat, lon) tuple
lat, lon = gc.geocode("Jl. Pemuda No.62, Semarang, Indonesia")

# Single address → full result (lat, lon, display_name, provider)
result = gc.geocode_full("Jl. Pemuda No.62, Semarang, Indonesia")
result.lat            # -6.9739
result.lon            # 110.4203
result.display_name   # "Jl. Pemuda No.62, Semarang, Jawa Tengah 50133, Indonesia"
result.provider       # "google"
result.ok             # True

# CSV → CSV (with incremental saves)
stats = gc.geocode_csv("input.csv", "output.csv", address_col="address")
# stats = {'total': 1000, 'geocoded': 950, 'already_ok': 30, 'failed': 20}

# DataFrame → DataFrame (requires geo-resolve[pandas])
df = gc.geocode_df(df, address_col="address", lat_col="latitude", lon_col="longitude")
```

### CLI

```bash
# CSV → CSV
uv run geo-resolve input.csv output.csv -p google -c id

# CSV → JSON
uv run geo-resolve input.csv output.json -p google

# Custom column names
uv run geo-resolve input.csv output.csv --address-col addr --lat-col lat --lon-col lng

# All options
uv run geo-resolve --help
```

| CLI flag | Default | Description |
|---|---|---|
| `-p`, `--provider` | Auto | Provider name |
| `-c`, `--country` | None | Country bias (ISO code) |
| `-f`, `--format` | Auto from extension | `csv` or `json` |
| `--address-col` | `address` | Address column name |
| `--lat-col` | `latitude` | Latitude column name |
| `--lon-col` | `longitude` | Longitude column name |
| `--no-cache` | False | Disable persistent cache |
| `--save-every` | 50 | Incremental save interval |
| `-q`, `--quiet` | False | Suppress output |

## Persistent cache

All results cached in SQLite at `~/.cache/geo-resolve/geocode.db`. Same address + provider combo is never re-requested. Re-runs and retries are instant.

```python
gc.cache_stats                               # {'total': 693, 'with_coords': 693, 'without_coords': 0}
gc.clear_cache()                             # clear all cached entries for this provider
gc.clear_cache(failures_only=True)           # clear only failed lookups (re-try them next run)

Geocoder(cache=False)                        # disable cache entirely
Geocoder(cache_path="/path/to/cache.db")     # custom cache location
```

## Adding a provider

One file, ~40 lines:

```python
from geo_resolve.providers.base import GeoProvider, GeoResult

class MyProvider(GeoProvider):
    name = "my_provider"
    default_rate_limit = 0.5

    def is_configured(self) -> bool:
        return bool(os.getenv("MY_PROVIDER_API_KEY"))

    def geocode(self, address: str, **kwargs) -> GeoResult:
        # Call your API here
        return GeoResult(lat=..., lon=..., provider=self.name)

# Use directly
gc = Geocoder(provider=MyProvider())

# Or add to PROVIDERS dict in providers/__init__.py to use by name
```

## Tests

```bash
# Unit tests (no API calls)
uv run pytest tests/ -k "not Integration"

# Integration tests (requires GOOGLE_MAPS_API_KEY in env)
uv run pytest tests/ -v
```

## All constructor options

| Parameter | Default | Description |
|---|---|---|
| `provider` | Auto | Provider name string or `GeoProvider` instance |
| `cache` | `True` | Persistent SQLite cache |
| `cache_path` | `~/.cache/geo-resolve/geocode.db` | Custom cache path |
| `country_bias` | `None` | ISO country code (e.g. `"id"`, `"gb"`, `"us"`) |
| `rate_limit` | Provider default | Override seconds between requests |
| `verbose` | `True` | Print progress |
