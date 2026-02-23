# F1 Real-Time Telemetry Streaming Pipeline

Replays historical F1 telemetry data (via FastF1) through Kafka, with one producer per driver running at configurable speed, consumed by a Dash dashboard showing a live track map and speed traces.

## Architecture

```
┌──────────┐     ┌───────────┐     ┌─────────────────┐
│  init    │────▶│  Kafka    │◀────│  producer (x5)  │
│ (prefetch│     │  (KRaft)  │     │  one per driver  │
│  FastF1) │     └─────┬─────┘     └─────────────────┘
└──────────┘           │
                       ▼
                ┌──────────────┐
                │    Dash      │
                │  Dashboard   │
                └──────────────┘
```

## Quick Start

```bash
docker compose up --build
```

Then open http://localhost:8050

The init container downloads race data (~30-60s on first run), then 5 producers begin replaying telemetry through Kafka at 10x speed. The Dash dashboard updates every 500ms via `dcc.Interval` callbacks to show:

- **Track map** with live driver positions
- **Speed trace** chart per driver
- **Lap data** table with times, sectors, and tyre compound

## Configuration

Edit `config.env` to change the race or speed:

| Variable | Default | Description |
|----------|---------|-------------|
| `F1_SEASON` | 2024 | Season year |
| `F1_EVENT` | Monaco | Grand Prix name |
| `F1_SESSION` | R | Session type (R=Race, Q=Qualifying, FP1/FP2/FP3) |
| `SPEED_MULTIPLIER` | 10 | Replay speed (10 = 10x real-time) |
| `NUM_DRIVERS` | 5 | Number of top finishers to track |

## Project Structure

```
├── docker-compose.yml          # All services orchestration
├── config.env                  # Race selection and Kafka settings
├── init/
│   ├── prefetch.py             # Downloads FastF1 data, writes manifest.json
│   └── Dockerfile
├── producer/
│   ├── producer.py             # Replays one driver's telemetry to Kafka
│   └── Dockerfile
└── dashboard/
    ├── app.py                  # Dash entrypoint
    ├── consumer.py             # Kafka consumer wrapper
    ├── track_map.py            # Plotly track figure with driver positions
    ├── telemetry_charts.py     # Speed trace line chart
    └── Dockerfile
```

## Kafka Topics

| Topic | Key | Content |
|-------|-----|---------|
| `f1.telemetry` | driver number | Speed, RPM, Throttle, Brake, DRS, Gear, X, Y, Z |
| `f1.laps` | driver number | LapNumber, LapTime, Sectors, Compound, Position |

## Stopping

```bash
docker compose down -v
```

The `-v` flag removes the data volume. Omit it to keep cached FastF1 data for faster restarts.
