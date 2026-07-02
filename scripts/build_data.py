"""
Build compact JSON data files for the weather dashboard.

Fetches full daily history for a set of KNMI stations via knmi_weather.py
and writes one JSON file per station plus an index file. The JSON format is
column-oriented and assumes one entry per calendar day (missing days are
padded with null), so the client can reconstruct dates from `start` + index:

    {
      "station": "260",
      "name": "De Bilt",
      "start": "1901-01-01",
      "end": "2026-06-30",
      "n": 45837,
      "series": {"temp_avg": [...], "temp_min": [...], ...}
    }

Usage:
    python scripts/build_data.py [output_dir]
"""

import json
import math
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from knmi_weather import DAILY_COLUMNS, get_daily

# Stations shown in the dashboard: (id, display name)
DASHBOARD_STATIONS = [
    ("260", "De Bilt"),
    ("240", "Schiphol"),
    ("344", "Rotterdam"),
    ("370", "Eindhoven"),
    ("380", "Maastricht"),
    ("350", "Gilze-Rijen"),
    ("280", "Groningen (Eelde)"),
    ("270", "Leeuwarden"),
    ("310", "Vlissingen"),
    ("290", "Twenthe"),
]

VARIABLES = list(DAILY_COLUMNS.values())


def build_station(station_id: str, name: str) -> dict:
    df = get_daily(start="1900-01-01", columns="all", station=station_id)
    df = df.dropna(subset=["date"]).sort_values("date")

    # Reindex to a contiguous daily range so the client can derive dates.
    full_range = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
    df = df.set_index("date").reindex(full_range)

    def encode(value):
        return None if value is None or (isinstance(value, float) and math.isnan(value)) else round(value, 1)

    series = {}
    for var in VARIABLES:
        if var in df.columns:
            series[var] = [encode(v) for v in df[var].tolist()]

    return {
        "station": station_id,
        "name": name,
        "start": full_range[0].strftime("%Y-%m-%d"),
        "end": full_range[-1].strftime("%Y-%m-%d"),
        "n": len(full_range),
        "series": series,
    }


def main():
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "dashboard" / "data"
    out_dir.mkdir(parents=True, exist_ok=True)

    index = {"variables": VARIABLES, "stations": []}
    for station_id, name in DASHBOARD_STATIONS:
        print(f"Fetching {name} ({station_id})...", flush=True)
        try:
            data = build_station(station_id, name)
        except Exception as e:
            print(f"  skipped: {e}", file=sys.stderr)
            continue
        path = out_dir / f"daily_{station_id}.json"
        path.write_text(json.dumps(data, separators=(",", ":")))
        size_mb = path.stat().st_size / 1e6
        print(f"  {data['start']} .. {data['end']} ({data['n']} days, {size_mb:.1f} MB)")
        index["stations"].append({
            "id": station_id,
            "name": name,
            "start": data["start"],
            "end": data["end"],
        })

    if not index["stations"]:
        sys.exit("No station data could be built.")
    (out_dir / "index.json").write_text(json.dumps(index, separators=(",", ":")))
    print(f"Wrote {len(index['stations'])} stations to {out_dir}")


if __name__ == "__main__":
    main()
