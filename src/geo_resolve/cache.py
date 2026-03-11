"""Persistent SQLite cache for geocoding results."""

import sqlite3
import time
from pathlib import Path

from geo_resolve.providers.base import GeoResult

DEFAULT_CACHE_PATH = Path.home() / ".cache" / "geo-resolve" / "geocode.db"


class GeoCache:
    """SQLite-backed persistent geocoding cache.

    Same address + provider combo is never re-geocoded.
    Cache survives across runs, projects, and reboots.
    """

    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else DEFAULT_CACHE_PATH
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path))
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS cache (
                address TEXT NOT NULL,
                provider TEXT NOT NULL,
                lat REAL,
                lon REAL,
                display_name TEXT DEFAULT '',
                created_at REAL NOT NULL,
                PRIMARY KEY (address, provider)
            )
        """)
        self._conn.commit()

    def get(self, address: str, provider: str) -> GeoResult | None:
        row = self._conn.execute(
            "SELECT lat, lon, display_name FROM cache WHERE address = ? AND provider = ?",
            (address.strip().lower(), provider),
        ).fetchone()
        if row is not None:
            return GeoResult(lat=row[0], lon=row[1], display_name=row[2] or "", provider=provider)
        return None

    def put(self, address: str, result: GeoResult) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO cache (address, provider, lat, lon, display_name, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (address.strip().lower(), result.provider, result.lat, result.lon,
             result.display_name, time.time()),
        )
        self._conn.commit()

    def stats(self) -> dict:
        row = self._conn.execute("SELECT COUNT(*), COUNT(lat) FROM cache").fetchone()
        return {"total": row[0], "with_coords": row[1], "without_coords": row[0] - row[1]}

    def clear(self, provider: str | None = None, failures_only: bool = False) -> int:
        """Clear cache entries. Returns number of rows deleted.

        Args:
            provider: Only clear entries for this provider. None = all.
            failures_only: Only clear entries where lat/lon is NULL (failed lookups).
        """
        conditions = []
        params: list = []
        if provider:
            conditions.append("provider = ?")
            params.append(provider)
        if failures_only:
            conditions.append("lat IS NULL")
        where = f" WHERE {' AND '.join(conditions)}" if conditions else ""
        cursor = self._conn.execute(f"DELETE FROM cache{where}", params)
        self._conn.commit()
        return cursor.rowcount

    def close(self):
        self._conn.close()
