"""Prefetch FastF1 session data and write a manifest for producers."""

import json
import os
import sys

import fastf1
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(PROJECT_ROOT, "data", "f1cache")
MANIFEST_PATH = os.path.join(CACHE_DIR, "manifest.json")

SEASON = int(os.environ.get("F1_SEASON", 2024))
EVENT = os.environ.get("F1_EVENT", "British Grand Prix")
SESSION_TYPE = os.environ.get("F1_SESSION", "R")
NUM_DRIVERS = int(os.environ.get("NUM_DRIVERS", 5))


def main():
    os.makedirs(CACHE_DIR, exist_ok=True)
    fastf1.Cache.enable_cache(CACHE_DIR)

    print(f"Loading session: {SEASON} {EVENT} {SESSION_TYPE}")
    session = fastf1.get_session(SEASON, EVENT, SESSION_TYPE)
    session.load(telemetry=True, laps=True, weather=False, messages=False)

    # Pick top N finishers
    results = session.results
    if results is None or results.empty:
        print("ERROR: No results found for this session.", file=sys.stderr)
        sys.exit(1)

    top_drivers = (
        results.sort_values("Position")
        .head(NUM_DRIVERS)
    )

    driver_list = []
    for _, row in top_drivers.iterrows():
        driver_list.append({
            "number": str(row["DriverNumber"]),
            "abbreviation": row["Abbreviation"],
            "full_name": row["FullName"],
            "team": row["TeamName"],
        })

    # Extract circuit coordinates from the fastest lap for track outline
    fastest_lap = session.laps.pick_fastest()
    telemetry = fastest_lap.get_telemetry()
    track_x = telemetry["X"].values
    track_y = telemetry["Y"].values

    track_coords = {
        "x": track_x.tolist(),
        "y": track_y.tolist(),
    }

    manifest = {
        "season": SEASON,
        "event": EVENT,
        "session": SESSION_TYPE,
        "drivers": driver_list,
        "track": track_coords,
    }

    # Sanitize any NaN/Inf values before writing JSON
    def sanitize(obj):
        if isinstance(obj, float):
            if np.isnan(obj) or np.isinf(obj):
                return None
            return obj
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [sanitize(v) for v in obj]
        return obj

    manifest = sanitize(manifest)

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

    abbrevs = [d["abbreviation"] for d in driver_list]
    print(f"Prefetch complete. {len(driver_list)} drivers: {abbrevs}")


if __name__ == "__main__":
    main()
