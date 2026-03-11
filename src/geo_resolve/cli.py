"""CLI entry point: geo-resolve input.csv output.csv --provider google"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="geo-resolve",
        description="Geocode addresses in a CSV file",
    )
    parser.add_argument("input", help="Input CSV file path")
    parser.add_argument("output", help="Output CSV file path")
    parser.add_argument("--provider", "-p", default=None, help="Geocoding provider (google, nominatim). Auto-selects if omitted.")
    parser.add_argument("--address-col", default="address", help="Address column name (default: address)")
    parser.add_argument("--lat-col", default="latitude", help="Latitude column name (default: latitude)")
    parser.add_argument("--lon-col", default="longitude", help="Longitude column name (default: longitude)")
    parser.add_argument("--country", "-c", default=None, help="Country bias code (e.g. 'id' for Indonesia)")
    parser.add_argument("--no-cache", action="store_true", help="Disable persistent cache")
    parser.add_argument("--save-every", type=int, default=50, help="Save progress every N rows (default: 50)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output")

    args = parser.parse_args()

    from geo_resolve import Geocoder

    gc = Geocoder(
        provider=args.provider,
        cache=not args.no_cache,
        country_bias=args.country,
        verbose=not args.quiet,
    )

    stats = gc.geocode_csv(
        args.input,
        args.output,
        address_col=args.address_col,
        lat_col=args.lat_col,
        lon_col=args.lon_col,
        save_every=args.save_every,
    )

    if stats["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
