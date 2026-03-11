"""Main Geocoder class — the public API."""

from __future__ import annotations

import csv
import os
import time
from pathlib import Path

from dotenv import load_dotenv

from geo_resolve.cache import GeoCache
from geo_resolve.providers import PROVIDERS, GeoProvider
from geo_resolve.providers.base import GeoResult

load_dotenv()


class Geocoder:
    """Provider-agnostic geocoder with caching, rate limiting, and batch support.

    Usage:
        gc = Geocoder()                        # auto-selects provider
        gc = Geocoder(provider="google")       # explicit
        gc = Geocoder(provider="nominatim")    # free

        lat, lon = gc.geocode("123 Main St, Jakarta")

        gc.geocode_csv("in.csv", "out.csv", address_col="address")
    """

    def __init__(
        self,
        provider: str | GeoProvider | None = None,
        cache: bool = True,
        cache_path: str | Path | None = None,
        country_bias: str | None = None,
        rate_limit: float | None = None,
        verbose: bool = True,
        **provider_kwargs,
    ):
        self._verbose = verbose
        self._country_bias = country_bias
        self._last_request: float = 0

        # Resolve provider
        if isinstance(provider, GeoProvider):
            self._provider = provider
        else:
            self._provider = self._auto_select(provider, **provider_kwargs)

        self._cache = GeoCache(cache_path) if cache else None
        self._rate_limit = rate_limit if rate_limit is not None else self._provider.default_rate_limit

    def _auto_select(self, name: str | None, **kwargs) -> GeoProvider:
        if name:
            cls = PROVIDERS.get(name)
            if not cls:
                raise ValueError(f"Unknown provider {name!r}. Available: {list(PROVIDERS)}")
            return cls(**kwargs)

        # Auto-select: prefer Google if configured, else Nominatim
        for pname in ("google", "nominatim"):
            cls = PROVIDERS[pname]
            inst = cls(**kwargs)
            if inst.is_configured():
                if self._verbose:
                    print(f"[geo-resolve] auto-selected provider: {pname}")
                return inst

        raise RuntimeError("No geocoding provider available. Set GOOGLE_MAPS_API_KEY or use provider='nominatim'.")

    def _rate_wait(self):
        if self._rate_limit > 0:
            elapsed = time.time() - self._last_request
            if elapsed < self._rate_limit:
                time.sleep(self._rate_limit - elapsed)
        self._last_request = time.time()

    def geocode(self, address: str, **kwargs) -> tuple[float | None, float | None]:
        """Geocode a single address. Returns (lat, lon) tuple."""
        if not address or not address.strip():
            return None, None

        merged = {"country_bias": self._country_bias}
        merged.update(kwargs)

        # Check cache
        if self._cache:
            cached = self._cache.get(address, self._provider.name)
            if cached is not None:
                return cached.lat, cached.lon

        # Call provider
        self._rate_wait()
        result = self._provider.geocode(address, **merged)

        # Store in cache (even failures, to avoid re-requesting)
        if self._cache:
            self._cache.put(address, result)

        return result.lat, result.lon

    def geocode_full(self, address: str, **kwargs) -> GeoResult:
        """Geocode with full result (lat, lon, display_name, provider)."""
        if not address or not address.strip():
            return GeoResult(provider=self._provider.name)

        merged = {"country_bias": self._country_bias}
        merged.update(kwargs)

        if self._cache:
            cached = self._cache.get(address, self._provider.name)
            if cached is not None:
                return cached

        self._rate_wait()
        result = self._provider.geocode(address, **merged)

        if self._cache:
            self._cache.put(address, result)

        return result

    def geocode_csv(
        self,
        input_path: str | Path,
        output_path: str | Path,
        address_col: str = "address",
        lat_col: str = "latitude",
        lon_col: str = "longitude",
        save_every: int = 50,
        **kwargs,
    ) -> dict:
        """Geocode a CSV file. Writes results incrementally.

        Returns dict with stats: {total, geocoded, cached, failed}.
        """
        input_path = Path(input_path)
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        rows = []
        with open(input_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = list(reader.fieldnames or [])
            for r in reader:
                rows.append(r)

        # Ensure lat/lon columns exist
        if lat_col not in fieldnames:
            fieldnames.append(lat_col)
        if lon_col not in fieldnames:
            fieldnames.append(lon_col)

        stats = {"total": len(rows), "already_ok": 0, "geocoded": 0, "cached": 0, "failed": 0}
        pending = 0

        for i, row in enumerate(rows):
            lat_val = row.get(lat_col, "").strip()
            lon_val = row.get(lon_col, "").strip()
            addr = row.get(address_col, "").strip()

            # Skip rows that already have coordinates
            if lat_val and lon_val:
                try:
                    float(lat_val)
                    float(lon_val)
                    stats["already_ok"] += 1
                    continue
                except ValueError:
                    pass

            if not addr:
                stats["failed"] += 1
                continue

            lat, lon = self.geocode(addr, **kwargs)
            if lat is not None and lon is not None:
                rows[i][lat_col] = str(lat)
                rows[i][lon_col] = str(lon)
                stats["geocoded"] += 1
            else:
                stats["failed"] += 1

            pending += 1

            # Incremental save
            if pending >= save_every:
                self._write_csv(output_path, fieldnames, rows)
                pending = 0
                if self._verbose:
                    done = stats["geocoded"] + stats["failed"] + stats["already_ok"]
                    print(f"  [{done}/{stats['total']}] geocoded={stats['geocoded']} failed={stats['failed']}", flush=True)

        # Final save
        self._write_csv(output_path, fieldnames, rows)

        if self._verbose:
            print(f"\nDone: {stats['geocoded']} geocoded, {stats['failed']} failed, "
                  f"{stats['already_ok']} already had coords", flush=True)
            print(f"Wrote {output_path}", flush=True)

        return stats

    def geocode_df(self, df, address_col="address", lat_col="latitude", lon_col="longitude", **kwargs):
        """Geocode a pandas DataFrame. Returns a new DataFrame with coords filled in.

        Requires: pip install geo-resolve[pandas]
        """
        import pandas as pd

        df = df.copy()
        if lat_col not in df.columns:
            df[lat_col] = None
        if lon_col not in df.columns:
            df[lon_col] = None

        missing = df[
            (df[address_col].notna()) & (df[address_col].str.strip() != "")
            & ((df[lat_col].isna()) | (df[lon_col].isna()))
        ]

        if self._verbose:
            print(f"[geo-resolve] {len(missing)} rows need geocoding out of {len(df)}", flush=True)

        for idx in missing.index:
            addr = str(df.at[idx, address_col])
            lat, lon = self.geocode(addr, **kwargs)
            if lat is not None:
                df.at[idx, lat_col] = lat
                df.at[idx, lon_col] = lon

        return df

    @staticmethod
    def _write_csv(path: Path, fieldnames: list[str], rows: list[dict]):
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)

    @property
    def cache_stats(self) -> dict | None:
        return self._cache.stats() if self._cache else None

    @property
    def provider_name(self) -> str:
        return self._provider.name
