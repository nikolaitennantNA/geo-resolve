"""CLI entry point: geo-resolve input.csv output.csv --provider google"""

import argparse
import json
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="geo-resolve",
        description="Geocode addresses in a CSV file",
    )
    parser.add_argument("input", help="Input CSV file")
    parser.add_argument("output", help="Output file (.csv or .json)")
    parser.add_argument("--provider", "-p", default=None,
                        help="Geocoding provider (google, google_places, google_validation, nominatim, opencage, locationiq)")
    parser.add_argument("--address-col", default="address", help="Address column (default: address)")
    parser.add_argument("--lat-col", default="latitude", help="Latitude column (default: latitude)")
    parser.add_argument("--lon-col", default="longitude", help="Longitude column (default: longitude)")
    parser.add_argument("--country", "-c", default=None, help="Country bias code (e.g. 'id')")
    parser.add_argument("--no-cache", action="store_true", help="Disable persistent cache")
    parser.add_argument("--save-every", type=int, default=50, help="Save progress every N rows (default: 50)")
    parser.add_argument("--format", "-f", choices=["csv", "json"], default=None,
                        help="Output format (auto-detected from extension)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress progress output")

    args = parser.parse_args()

    from pathlib import Path
    from geo_resolve import Geocoder

    gc = Geocoder(
        provider=args.provider,
        cache=not args.no_cache,
        country_bias=args.country,
        verbose=not args.quiet,
    )

    # Auto-detect format from extension
    out_ext = Path(args.output).suffix.lower()
    fmt = args.format or ("json" if out_ext == ".json" else "csv")

    if fmt == "csv":
        stats = gc.geocode_csv(
            args.input, args.output,
            address_col=args.address_col,
            lat_col=args.lat_col,
            lon_col=args.lon_col,
            save_every=args.save_every,
        )
    else:
        # JSON output — read CSV, geocode, write JSON
        import csv
        rows = []
        with open(args.input, "r", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rows.append(r)

        results = []
        for i, row in enumerate(rows):
            addr = row.get(args.address_col, "").strip()
            lat_val = row.get(args.lat_col, "").strip()
            lon_val = row.get(args.lon_col, "").strip()

            # Skip rows that already have coords
            if lat_val and lon_val:
                try:
                    float(lat_val)
                    float(lon_val)
                    results.append(row)
                    continue
                except ValueError:
                    pass

            if addr:
                result = gc.geocode_full(addr)
                if result.ok:
                    row[args.lat_col] = result.lat
                    row[args.lon_col] = result.lon
                    row["_geo_display_name"] = result.display_name
                    row["_geo_provider"] = result.provider

            results.append(row)

            if not args.quiet and (i + 1) % 50 == 0:
                print(f"  [{i+1}/{len(rows)}]", flush=True)

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

        if not args.quiet:
            print(f"Wrote {len(results)} rows to {args.output}", flush=True)

        stats = {"total": len(rows)}

    if stats.get("failed", 0) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
