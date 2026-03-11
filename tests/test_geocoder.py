"""Tests for geo-resolve. Unit tests use a mock provider; integration tests hit real APIs."""

import csv
import json
import os
import tempfile
from pathlib import Path

import pytest

from geo_resolve import Geocoder
from geo_resolve.cache import GeoCache
from geo_resolve.providers.base import GeoProvider, GeoResult


# ---------------------------------------------------------------------------
# Mock provider for unit tests (no API calls)
# ---------------------------------------------------------------------------

class MockProvider(GeoProvider):
    """Returns deterministic results for known addresses, None for unknown."""
    name = "mock"
    default_rate_limit = 0

    KNOWN = {
        "jakarta": GeoResult(lat=-6.2088, lon=106.8456, display_name="Jakarta, Indonesia", provider="mock"),
        "semarang": GeoResult(lat=-6.9666, lon=110.4196, display_name="Semarang, Indonesia", provider="mock"),
        "london": GeoResult(lat=51.5074, lon=-0.1278, display_name="London, UK", provider="mock"),
    }

    def is_configured(self) -> bool:
        return True

    def geocode(self, address: str, **kwargs) -> GeoResult:
        key = address.strip().lower()
        for name, result in self.KNOWN.items():
            if name in key:
                return result
        return GeoResult(provider=self.name)


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

class TestGeocoderUnit:
    def test_single_geocode(self):
        gc = Geocoder(provider=MockProvider(), cache=False)
        lat, lon = gc.geocode("Jakarta, Indonesia")
        assert lat == pytest.approx(-6.2088)
        assert lon == pytest.approx(106.8456)

    def test_unknown_address(self):
        gc = Geocoder(provider=MockProvider(), cache=False)
        lat, lon = gc.geocode("Nowhere, Fictional Country")
        assert lat is None
        assert lon is None

    def test_empty_address(self):
        gc = Geocoder(provider=MockProvider(), cache=False)
        lat, lon = gc.geocode("")
        assert lat is None
        assert lon is None

    def test_geocode_full(self):
        gc = Geocoder(provider=MockProvider(), cache=False)
        result = gc.geocode_full("Semarang")
        assert result.ok
        assert result.lat == pytest.approx(-6.9666)
        assert result.display_name == "Semarang, Indonesia"
        assert result.provider == "mock"

    def test_provider_name(self):
        gc = Geocoder(provider=MockProvider(), cache=False)
        assert gc.provider_name == "mock"


class TestCache:
    def test_cache_hit(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "test.db"
            gc = Geocoder(provider=MockProvider(), cache=True, cache_path=cache_path)

            # First call — miss, calls provider
            lat1, lon1 = gc.geocode("Jakarta")
            assert lat1 == pytest.approx(-6.2088)

            # Second call — cache hit, same result
            lat2, lon2 = gc.geocode("Jakarta")
            assert lat2 == pytest.approx(-6.2088)

            assert gc.cache_stats["total"] == 1
            assert gc.cache_stats["with_coords"] == 1

    def test_cache_stores_failures(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "test.db"
            gc = Geocoder(provider=MockProvider(), cache=True, cache_path=cache_path)

            gc.geocode("Unknown Address")
            assert gc.cache_stats["without_coords"] == 1

    def test_clear_cache_failures_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "test.db"
            gc = Geocoder(provider=MockProvider(), cache=True, cache_path=cache_path)

            gc.geocode("Jakarta")
            gc.geocode("Unknown Address")
            assert gc.cache_stats["total"] == 2

            deleted = gc.clear_cache(failures_only=True)
            assert deleted == 1
            assert gc.cache_stats["total"] == 1
            assert gc.cache_stats["with_coords"] == 1

    def test_clear_cache_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_path = Path(tmp) / "test.db"
            gc = Geocoder(provider=MockProvider(), cache=True, cache_path=cache_path)

            gc.geocode("Jakarta")
            gc.geocode("London")
            deleted = gc.clear_cache()
            assert deleted == 2
            assert gc.cache_stats["total"] == 0


class TestCSV:
    def _make_csv(self, tmp_dir: str, rows: list[dict]) -> Path:
        path = Path(tmp_dir) / "input.csv"
        fieldnames = list(rows[0].keys())
        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_geocode_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = self._make_csv(tmp, [
                {"address": "Jakarta, Indonesia", "latitude": "", "longitude": ""},
                {"address": "Semarang", "latitude": "", "longitude": ""},
                {"address": "Unknown Place", "latitude": "", "longitude": ""},
            ])
            output_path = Path(tmp) / "output.csv"

            gc = Geocoder(provider=MockProvider(), cache=False, verbose=False)
            stats = gc.geocode_csv(input_path, output_path, address_col="address")

            assert stats["total"] == 3
            assert stats["geocoded"] == 2
            assert stats["failed"] == 1

            # Read output and verify
            with open(output_path) as f:
                rows = list(csv.DictReader(f))
            assert rows[0]["latitude"] == str(-6.2088)
            assert rows[1]["latitude"] == str(-6.9666)
            assert rows[2]["latitude"] == ""

    def test_geocode_csv_skips_existing(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = self._make_csv(tmp, [
                {"address": "Jakarta", "latitude": "1.0", "longitude": "2.0"},
                {"address": "Semarang", "latitude": "", "longitude": ""},
            ])
            output_path = Path(tmp) / "output.csv"

            gc = Geocoder(provider=MockProvider(), cache=False, verbose=False)
            stats = gc.geocode_csv(input_path, output_path, address_col="address")

            assert stats["already_ok"] == 1
            assert stats["geocoded"] == 1

            with open(output_path) as f:
                rows = list(csv.DictReader(f))
            # Existing coords preserved
            assert rows[0]["latitude"] == "1.0"


class TestCLI:
    def test_csv_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            input_path = Path(tmp) / "input.csv"
            output_path = Path(tmp) / "output.csv"
            with open(input_path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["address", "latitude", "longitude"])
                writer.writeheader()
                writer.writerow({"address": "Jakarta", "latitude": "", "longitude": ""})

            # Test via Python import (not subprocess, to use MockProvider)
            gc = Geocoder(provider=MockProvider(), cache=False, verbose=False)
            stats = gc.geocode_csv(input_path, output_path, address_col="address")
            assert stats["geocoded"] == 1


# ---------------------------------------------------------------------------
# Integration tests (hit real APIs — skip if no key)
# ---------------------------------------------------------------------------

HAS_GOOGLE_KEY = bool(os.getenv("GOOGLE_MAPS_API_KEY") or os.getenv("GOOGLE_PLACES_API_KEY"))


@pytest.mark.skipif(not HAS_GOOGLE_KEY, reason="GOOGLE_MAPS_API_KEY not set")
class TestGoogleIntegration:
    def test_google_geocoding(self):
        """Google Geocoding API — address → coords. The main workhorse."""
        gc = Geocoder(provider="google", cache=False, verbose=False)
        lat, lon = gc.geocode("Jl. Pemuda No.62, Semarang, Indonesia")
        assert lat is not None
        assert -8 < lat < -6  # Semarang area
        assert 109 < lon < 112

    @pytest.mark.skip(reason="Requires Places API enabled in Google Cloud Console")
    def test_google_places(self):
        """Google Places Text Search — business name query → listing + coords."""
        gc = Geocoder(provider="google_places", cache=False, verbose=False)
        result = gc.geocode_full("Bank BRI Semarang")
        assert result.ok
        assert result.display_name

    @pytest.mark.skip(reason="Requires Address Validation API enabled in Google Cloud Console")
    def test_google_validation(self):
        """Google Address Validation — corrects messy addresses + coords."""
        gc = Geocoder(provider="google_validation", cache=False, verbose=False, country_bias="id")
        lat, lon = gc.geocode("Jl. Pemuda 62, Semarang")
        assert lat is not None


class TestNominatimIntegration:
    def test_nominatim(self):
        gc = Geocoder(provider="nominatim", cache=False, verbose=False, country_bias="id")
        lat, lon = gc.geocode("Semarang, Jawa Tengah, Indonesia")
        assert lat is not None
        assert -8 < lat < -6
        assert 109 < lon < 112
