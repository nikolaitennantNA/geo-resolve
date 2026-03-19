# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A provider-agnostic geocoding library that converts addresses into geographic coordinates. Supports multiple backends (Google Maps, Nominatim, OpenCage, LocationIQ), plus specialized providers for business search (Google Places) and address validation (Google Address Validation). Features persistent SQLite caching, rate limiting, and batch CSV/DataFrame processing.

Used by the `asset-discovery` pipeline's optional Geocode stage.

## Commands

```bash
# Install
uv sync

# Run unit tests (no API calls)
uv run pytest tests/ -k "not Integration"

# Run all tests (integration tests need GOOGLE_MAPS_API_KEY)
uv run pytest tests/ -v

# CLI usage
uv run geo-resolve input.csv output.csv -p google -c us
uv run geo-resolve input.csv output.csv --provider nominatim
uv run geo-resolve input.csv output.json --address-col addr --lat-col lat --lon-col lng
```

## Architecture

### Key Files

| File | Role |
|---|---|
| `src/geo_resolve/__init__.py` | Exports `Geocoder` class |
| `src/geo_resolve/geocoder.py` | Main `Geocoder` class — `geocode()`, `geocode_full()`, `geocode_csv()`, `geocode_df()` |
| `src/geo_resolve/cache.py` | `GeoCache` — SQLite persistent cache (`~/.cache/geo-resolve/geocode.db`) |
| `src/geo_resolve/cli.py` | CLI entry point (`geo-resolve` command) |
| `src/geo_resolve/providers/base.py` | Abstract `GeoProvider` and `GeoResult` classes |
| `src/geo_resolve/providers/google.py` | Google Maps Geocoding API |
| `src/geo_resolve/providers/google_places.py` | Google Places Text Search API |
| `src/geo_resolve/providers/google_validation.py` | Google Address Validation API |
| `src/geo_resolve/providers/nominatim.py` | OSM Nominatim (free, no key needed) |
| `src/geo_resolve/providers/opencage.py` | OpenCage Geocoding API |
| `src/geo_resolve/providers/locationiq.py` | LocationIQ API |

### Providers

| Provider | Key Env Var | Rate Limit | Cost |
|---|---|---|---|
| `google` | `GOOGLE_MAPS_API_KEY` | 50 QPS | $5/1K |
| `google_places` | `GOOGLE_MAPS_API_KEY` | 50 QPS | $32/1K |
| `google_validation` | `GOOGLE_MAPS_API_KEY` | 50 QPS | $17/1K |
| `nominatim` | (none) | 1 QPS | Free |
| `opencage` | `OPENCAGE_API_KEY` | 1 QPS | Free (2.5K/day) |
| `locationiq` | `LOCATIONIQ_API_KEY` | 2 QPS | Free (5K/day) |

Auto-selection order: Google (if key set) → Nominatim (always available).

### Key Patterns

- **Provider abstraction** — All providers implement `GeoProvider` with `geocode(address) -> GeoResult` and `is_configured() -> bool`
- **Persistent SQLite cache** — Keyed on `(address.lower(), provider)`. Stores successes AND failures to avoid re-requesting.
- **Rate limiting** — Per-provider configurable delay between requests via `_rate_wait()`
- **Batch processing** — CSV: incremental writes every `save_every` rows (default 50). DataFrame: in-place coordinate filling. Both skip rows with existing coordinates.
- **Graceful errors** — Provider exceptions caught and logged; return empty `GeoResult`. Cache stores failures.
- **Country bias** — Optional ISO country code parameter biases results for ambiguous addresses

## Conventions

- Python 3.13+, synchronous (uses `requests`, not async)
- Pydantic-free — uses plain dataclasses for models
- `python-dotenv` for `.env` loading
- pytest for testing; `MockProvider` in test file for unit tests
- `pandas` optional dependency for DataFrame support
