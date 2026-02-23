"""Plotly speed trace chart for driver telemetry."""

import plotly.graph_objects as go

from track_map import TEAM_COLORS, FALLBACK_COLORS


def build_speed_chart(telemetry_history, driver_info_map):
    """
    Build a speed trace line chart for all drivers.

    Args:
        telemetry_history: dict mapping driver_number -> list of telemetry dicts
            Each dict has at least "speed" and an implicit index (sample order).
        driver_info_map: dict mapping driver_number -> {"abbreviation": ..., "team": ...}
    """
    fig = go.Figure()

    for i, (driver_num, samples) in enumerate(telemetry_history.items()):
        if not samples:
            continue

        info = driver_info_map.get(driver_num, {})
        team = info.get("team", "")
        abbr = info.get("abbreviation", driver_num)
        color = TEAM_COLORS.get(team, FALLBACK_COLORS[i % len(FALLBACK_COLORS)])

        speeds = [s.get("speed") or 0 for s in samples]
        x_vals = list(range(len(speeds)))

        fig.add_trace(go.Scatter(
            x=x_vals,
            y=speeds,
            mode="lines",
            name=abbr,
            line=dict(color=color, width=2),
        ))

    fig.update_layout(
        xaxis=dict(title="Sample", color="#AAAAAA", gridcolor="#333333"),
        yaxis=dict(title="Speed (km/h)", color="#AAAAAA", gridcolor="#333333"),
        margin=dict(l=50, r=20, t=30, b=40),
        height=500,
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        legend=dict(font=dict(color="white")),
        title=dict(text="Speed Trace", font=dict(color="white", size=16)),
    )

    return fig
