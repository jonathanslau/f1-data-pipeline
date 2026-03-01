"""Dash dashboard for real-time F1 telemetry visualization."""

import json
import os
from collections import deque

from dash import Dash, html, dcc, dash_table, Input, Output, callback

from consumer import TelemetryConsumer
from track_map import build_track_figure
from telemetry_charts import build_speed_chart

KAFKA_SERVERS = os.environ.get("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
TELEMETRY_TOPIC = os.environ.get("KAFKA_TELEMETRY_TOPIC", "f1.telemetry")
LAPS_TOPIC = os.environ.get("KAFKA_LAPS_TOPIC", "f1.laps")
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(PROJECT_ROOT, "data", "f1cache")
MANIFEST_PATH = os.path.join(CACHE_DIR, "manifest.json")

MAX_HISTORY = 500
REFRESH_MS = 500

# --- Load manifest ---
manifest = None
try:
    with open(MANIFEST_PATH) as f:
        manifest = json.load(f)
except FileNotFoundError:
    pass

driver_info_map = {}
track_coords = {}
if manifest:
    for d in manifest["drivers"]:
        driver_info_map[d["number"]] = {
            "abbreviation": d["abbreviation"],
            "full_name": d["full_name"],
            "team": d["team"],
        }
    track_coords = manifest.get("track", {})

# --- Server-side state ---
positions = {}  # driver_number -> latest {x, y, speed, abbreviation}
telemetry_history = {}  # driver_number -> deque of samples
lap_data = {}  # driver_number -> latest lap event dict

consumer = TelemetryConsumer(
    bootstrap_servers=KAFKA_SERVERS,
    topics=[TELEMETRY_TOPIC, LAPS_TOPIC],
)

# --- Dash app ---
app = Dash(__name__)

event_name = ""
if manifest:
    event_name = f"{manifest['season']} {manifest['event']} ({manifest['session']})"

app.layout = html.Div(
    style={"backgroundColor": "#0E1117", "minHeight": "100vh", "padding": "20px"},
    children=[
        dcc.Interval(id="interval", interval=REFRESH_MS, n_intervals=0),

        html.H1(
            f"F1 Live Telemetry — {event_name}",
            style={"color": "white", "textAlign": "center", "marginBottom": "20px",
                   "fontFamily": "sans-serif"},
        ),

        html.Div(
            style={"display": "flex", "gap": "20px"},
            children=[
                html.Div(dcc.Graph(id="track-map"), style={"flex": "1"}),
                html.Div(dcc.Graph(id="speed-chart"), style={"flex": "1"}),
            ],
        ),

        html.H2(
            "Lap Data",
            style={"color": "white", "marginTop": "20px", "fontFamily": "sans-serif"},
        ),
        html.Div(id="lap-table-container"),
    ],
)


def _poll_kafka():
    """Drain Kafka and update server-side state."""
    telemetry_msgs, lap_msgs = consumer.poll_batch(max_messages=300, timeout=0.0)

    for msg in telemetry_msgs:
        drv = msg.get("driver_number")
        if drv is None:
            continue
        positions[drv] = {
            "x": msg.get("x"),
            "y": msg.get("y"),
            "speed": msg.get("speed"),
            "abbreviation": msg.get("abbreviation", drv),
        }
        if drv not in telemetry_history:
            telemetry_history[drv] = deque(maxlen=MAX_HISTORY)
        telemetry_history[drv].append(msg)

    for msg in lap_msgs:
        drv = msg.get("driver_number")
        if drv is not None:
            lap_data[drv] = msg


@callback(
    Output("track-map", "figure"),
    Output("speed-chart", "figure"),
    Output("lap-table-container", "children"),
    Input("interval", "n_intervals"),
)
def update(_n):
    _poll_kafka()

    track_fig = build_track_figure(track_coords, positions, driver_info_map)
    speed_fig = build_speed_chart(
        {k: list(v) for k, v in telemetry_history.items()},
        driver_info_map,
    )

    if lap_data:
        cols = [
            "abbreviation", "lap_number", "lap_time",
            "sector1", "sector2", "sector3", "compound", "position",
        ]
        rows = sorted(lap_data.values(), key=lambda r: r.get("position", 99))
        # Filter to columns that exist
        available = [c for c in cols if c in rows[0]]
        table = dash_table.DataTable(
            data=[{c: r.get(c) for c in available} for r in rows],
            columns=[{"name": c.replace("_", " ").title(), "id": c} for c in available],
            style_table={"maxHeight": "300px", "overflowY": "auto"},
            style_header={"backgroundColor": "#1a1a2e", "color": "white", "fontWeight": "bold"},
            style_cell={"backgroundColor": "#16213e", "color": "white", "border": "1px solid #333",
                        "fontFamily": "monospace", "textAlign": "center"},
            page_size=20,
        )
    else:
        table = html.P("Waiting for lap data...", style={"color": "#888", "fontFamily": "sans-serif"})

    return track_fig, speed_fig, table


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)
