"""Provider-agnostic geocoding with persistent cache, rate limiting, and batch support.

Usage:
    from geo_resolve import Geocoder

    gc = Geocoder()                          # auto-selects provider from env
    gc = Geocoder(provider="google")         # explicit provider
    gc = Geocoder(provider="nominatim")      # free, no API key

    # Single address
    lat, lon = gc.geocode("123 Main St, Jakarta, Indonesia")

    # Batch CSV
    gc.geocode_csv("input.csv", "output.csv", address_col="address")

    # Batch DataFrame
    df = gc.geocode_df(df, address_col="address")
"""

from geo_resolve.geocoder import Geocoder

__all__ = ["Geocoder"]
__version__ = "0.1.0"
