"""Replay one driver's telemetry to Kafka at configurable speed."""

import json
import os
import sys
import time

import fastf1
import numpy as np
import pandas as pd
from confluent_kafka import Producer

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(PROJECT_ROOT, "data", "f1cache")
MANIFEST_PATH = os.path.join(CACHE_DIR, "manifest.json")

KAFKA_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TELEMETRY_TOPIC = os.environ.get("KAFKA_TELEMETRY_TOPIC", "f1.telemetry")
LAPS_TOPIC = os.environ.get("KAFKA_LAPS_TOPIC", "f1.laps")
SPEED_MULTIPLIER = float(os.environ.get("SPEED_MULTIPLIER", 10))
DRIVER_INDEX = int(os.environ.get("DRIVER_INDEX", 0))


def delivery_report(err, msg):
    if err is not None:
        print(f"Delivery failed: {err}", file=sys.stderr)


def safe_value(v):
    """Convert numpy/pandas types to JSON-safe Python types."""
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        f = float(v)
        if np.isnan(f) or np.isinf(f):
            return None
        return f
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, pd.Timestamp):
        return v.isoformat()
    if isinstance(v, pd.Timedelta):
        return v.total_seconds()
    if pd.isna(v):
        return None
    return v


def main():
    # Load manifest
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)

    if DRIVER_INDEX >= len(manifest["drivers"]):
        print(f"DRIVER_INDEX {DRIVER_INDEX} out of range ({len(manifest['drivers'])} drivers)")
        sys.exit(0)

    driver_info = manifest["drivers"][DRIVER_INDEX]
    driver_num = driver_info["number"]
    driver_abbr = driver_info["abbreviation"]

    print(f"Producer started for {driver_abbr} (#{driver_num})")

    # Load session from cache
    fastf1.Cache.enable_cache(CACHE_DIR)
    session = fastf1.get_session(
        manifest["season"], manifest["event"], manifest["session"]
    )
    session.load(telemetry=True, laps=True, weather=False, messages=False)

    # Get this driver's laps and telemetry
    driver_laps = session.laps.pick_drivers(int(driver_num))
    if driver_laps.empty:
        print(f"No laps found for driver {driver_abbr}", file=sys.stderr)
        sys.exit(1)

    # Create Kafka producer
    producer = Producer({
        "bootstrap.servers": KAFKA_SERVERS,
        "linger.ms": 5,
        "batch.num.messages": 100,
    })

    # Replay each lap
    for _, lap in driver_laps.iterrows():
        lap_number = int(lap["LapNumber"])

        try:
            telemetry = lap.get_telemetry()
        except Exception as e:
            print(f"  Skipping lap {lap_number}: {e}")
            continue

        if telemetry.empty:
            continue

        # Publish lap start event
        lap_msg = {
            "driver_number": driver_num,
            "abbreviation": driver_abbr,
            "lap_number": lap_number,
            "lap_time": safe_value(lap.get("LapTime")),
            "sector1": safe_value(lap.get("Sector1Time")),
            "sector2": safe_value(lap.get("Sector2Time")),
            "sector3": safe_value(lap.get("Sector3Time")),
            "compound": safe_value(lap.get("Compound")),
            "position": safe_value(lap.get("Position")),
        }
        producer.produce(
            LAPS_TOPIC,
            key=driver_num,
            value=json.dumps(lap_msg),
            callback=delivery_report,
        )

        print(f"  {driver_abbr} lap {lap_number}")

        # Replay telemetry rows with timing
        prev_time = None
        for _, row in telemetry.iterrows():
            # Build telemetry message
            msg = {
                "driver_number": driver_num,
                "abbreviation": driver_abbr,
                "lap_number": lap_number,
                "speed": safe_value(row.get("Speed")),
                "rpm": safe_value(row.get("RPM")),
                "throttle": safe_value(row.get("Throttle")),
                "brake": safe_value(row.get("Brake")),
                "drs": safe_value(row.get("DRS")),
                "gear": safe_value(row.get("nGear")),
                "x": safe_value(row.get("X")),
                "y": safe_value(row.get("Y")),
                "z": safe_value(row.get("Z")),
            }

            # Sleep to maintain replay timing
            current_time = row.get("SessionTime") or row.get("Time")
            if isinstance(current_time, pd.Timedelta):
                if prev_time is not None:
                    delta = (current_time - prev_time).total_seconds()
                    if 0 < delta < 5:  # cap to avoid huge gaps
                        time.sleep(delta / SPEED_MULTIPLIER)
                prev_time = current_time

            producer.produce(
                TELEMETRY_TOPIC,
                key=driver_num,
                value=json.dumps(msg),
                callback=delivery_report,
            )
            producer.poll(0)

        producer.flush()

    producer.flush()
    print(f"Producer finished for {driver_abbr}")


if __name__ == "__main__":
    main()
