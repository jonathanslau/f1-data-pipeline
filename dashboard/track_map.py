"""Plotly track map with driver position markers."""

import plotly.graph_objects as go

# Team color mapping (2024 season)
TEAM_COLORS = {
    "Red Bull Racing": "#3671C6",
    "Ferrari": "#E8002D",
    "McLaren": "#FF8000",
    "Mercedes": "#27F4D2",
    "Aston Martin": "#229971",
    "Alpine": "#FF87BC",
    "Williams": "#64C4FF",
    "RB": "#6692FF",
    "Kick Sauber": "#52E252",
    "Haas F1 Team": "#B6BABD",
}

# Fallback palette
FALLBACK_COLORS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
]


def build_track_figure(track_coords, driver_positions, driver_info_map):
    """
    Build a Plotly figure showing the track outline and driver positions.

    Args:
        track_coords: dict with "x" and "y" lists for the track outline
        driver_positions: dict mapping driver_number -> {"x": ..., "y": ..., "abbreviation": ...}
        driver_info_map: dict mapping driver_number -> {"abbreviation": ..., "team": ...}
    """
    fig = go.Figure()

    # Track outline
    if track_coords:
        # Close the loop
        x = track_coords["x"] + [track_coords["x"][0]]
        y = track_coords["y"] + [track_coords["y"][0]]
        fig.add_trace(go.Scatter(
            x=x, y=y,
            mode="lines",
            line=dict(color="#555555", width=6),
            name="Track",
            hoverinfo="skip",
        ))

    # Driver markers
    for i, (driver_num, pos) in enumerate(driver_positions.items()):
        if pos.get("x") is None or pos.get("y") is None:
            continue

        info = driver_info_map.get(driver_num, {})
        team = info.get("team", "")
        abbr = pos.get("abbreviation", driver_num)
        color = TEAM_COLORS.get(team, FALLBACK_COLORS[i % len(FALLBACK_COLORS)])

        fig.add_trace(go.Scatter(
            x=[pos["x"]],
            y=[pos["y"]],
            mode="markers+text",
            marker=dict(size=14, color=color, line=dict(width=2, color="white")),
            text=[abbr],
            textposition="top center",
            textfont=dict(size=11, color=color),
            name=abbr,
            hovertemplate=f"<b>{abbr}</b><br>Speed: {pos.get('speed', '?')} km/h<extra></extra>",
        ))

    fig.update_layout(
        showlegend=False,
        xaxis=dict(visible=False, scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False),
        margin=dict(l=0, r=0, t=30, b=0),
        height=500,
        paper_bgcolor="#0E1117",
        plot_bgcolor="#0E1117",
        title=dict(text="Track Map", font=dict(color="white", size=16)),
    )

    return fig
