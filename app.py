import base64
import io
import re
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

MAP_CONFIGS = {
    "AmbroseValley": {"scale": 900,  "origin_x": -370, "origin_z": -473, "image": "AmbroseValley_Minimap.png"},
    "GrandRift":     {"scale": 581,  "origin_x": -290, "origin_z": -290, "image": "GrandRift_Minimap.png"},
    "Lockdown":      {"scale": 1000, "origin_x": -500, "origin_z": -500, "image": "Lockdown_Minimap.jpg"},
}

EVENT_CATEGORIES = [
    {"events": {"Kill", "BotKill"},     "color": "#FF3B30", "label": "Kills"},
    {"events": {"Killed", "BotKilled"}, "color": "#1E5BFF", "label": "Deaths"},
    {"events": {"Loot"},                "color": "#34C759", "label": "Loot"},
    {"events": {"KilledByStorm"},       "color": "#FFD400", "label": "Storm Deaths"},
]

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)

IMG_SIZE = 1024


def _load_map_image(map_name: str):
    base_dir = Path(__file__).resolve().parent
    img_path = base_dir / "minimaps" / MAP_CONFIGS[map_name]["image"]
    if not img_path.exists():
        return None
    img = Image.open(img_path).convert("RGBA").resize((IMG_SIZE, IMG_SIZE))
    return np.array(img)


def _parse_ts(df):
    if "ts" not in df.columns:
        return pd.Series([pd.NaT] * len(df), index=df.index)
    ts = df["ts"]
    if pd.api.types.is_numeric_dtype(ts):
        return pd.to_datetime(ts, unit="ms", errors="coerce")
    coerced = pd.to_numeric(ts, errors="coerce")
    if coerced.notna().mean() > 0.5:
        return pd.to_datetime(coerced, unit="ms", errors="coerce")
    return pd.to_datetime(ts, errors="coerce")


def _is_human(uid_series):
    return uid_series.astype(str).map(lambda v: bool(UUID_RE.match(v)))


def _to_pixels(df, *, scale, origin_x, origin_z):
    df = df.copy()
    df["x"] = pd.to_numeric(df["x"], errors="coerce")
    df["z"] = pd.to_numeric(df["z"], errors="coerce")
    df["pixel_x"] = ((df["x"] - origin_x) / scale) * IMG_SIZE
    df["pixel_y"] = (1.0 - ((df["z"] - origin_z) / scale)) * IMG_SIZE
    return df


def _hex_rgba(hex_color, alpha):
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def build_figure(df_map, map_name, *, heatmap_mode, bins, max_points):
    fig = go.Figure()

    # ── MAP IMAGE ───────────────────────────────────────────────────────────
    img_array = _load_map_image(map_name)
    if img_array is not None:
        fig.add_trace(go.Image(z=img_array))
        fig.update_xaxes(range=[-0.5, IMG_SIZE - 0.5])
        fig.update_yaxes(range=[IMG_SIZE - 0.5, -0.5])
    else:
        st.warning("⚠️ Minimap image not found — check your `minimaps/` folder.")
        fig.update_xaxes(range=[0, IMG_SIZE])
        fig.update_yaxes(range=[IMG_SIZE, 0])
    # ────────────────────────────────────────────────────────────────────────

    fig.update_layout(
        height=700, width=700,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(
            itemsizing="constant",
            bgcolor="rgba(0,0,0,0.6)",
            font=dict(color="white"),
        ),
        xaxis=dict(showgrid=False, zeroline=False, title=""),
        yaxis=dict(showgrid=False, zeroline=False, title=""),
    )

    if df_map.empty:
        fig.update_layout(title=f"{map_name} — no data")
        return fig

    df_map = df_map.dropna(subset=["pixel_x", "pixel_y", "event", "user_id"])
    df_map["is_human"] = _is_human(df_map["user_id"])

    if not heatmap_mode and len(df_map) > max_points:
        df_map = df_map.sample(n=max_points, random_state=42)

    for cat in EVENT_CATEGORIES:
        df_cat = df_map[df_map["event"].isin(cat["events"])]
        if df_cat.empty:
            continue
        for group, mask, symbol in [
            ("Human", df_cat["is_human"],  "circle"),
            ("Bot",  ~df_cat["is_human"],  "x"),
        ]:
            df_g = df_cat[mask]
            if df_g.empty:
                continue
            if heatmap_mode:
                fig.add_trace(go.Histogram2d(
                    x=df_g["pixel_x"], y=df_g["pixel_y"],
                    nbinsx=bins, nbinsy=bins,
                    colorscale=[[0, "rgba(0,0,0,0)"],
                                [1, _hex_rgba(cat["color"], 0.75 if group == "Human" else 0.45)]],
                    showscale=False,
                    name=f"{cat['label']} ({group})",
                ))
            else:
                fig.add_trace(go.Scattergl(
                    x=df_g["pixel_x"], y=df_g["pixel_y"],
                    mode="markers",
                    marker=dict(
                        size=7 if group == "Human" else 5,
                        color=cat["color"],
                        symbol=symbol,
                        opacity=0.9,
                    ),
                    name=f"{cat['label']} ({group})",
                    hovertemplate="event=%{customdata[0]}<br>user=%{customdata[1]}<extra></extra>",
                    customdata=df_g[["event", "user_id"]].values,
                ))

    fig.update_layout(title=f"{map_name} — {'Heatmap' if heatmap_mode else 'Scatter'}")
    return fig


def main():
    st.set_page_config(page_title="LILA BLACK Map Viewer", layout="wide")
    st.title("LILA BLACK Map Viewer")
    st.caption("Player journey visualization — event dots and heatmaps on minimap.")

    base_dir    = Path(__file__).resolve().parent
    default_csv = base_dir / "all_events.csv"

    uploaded = st.file_uploader("Upload events CSV", type=["csv"])
    if uploaded is None:
        if default_csv.exists():
            df = pd.read_csv(default_csv, low_memory=False)
            st.info("Using default: `all_events.csv`")
        else:
            st.warning("Place `all_events.csv` next to `app.py`, or upload it above.")
            st.stop()
    else:
        df = pd.read_csv(uploaded, low_memory=False)

    required = {"map_id", "match_id", "user_id", "x", "z", "ts", "event"}
    missing  = required - set(df.columns)
    if missing:
        st.error(f"Missing columns: {sorted(missing)}")
        st.stop()

    df = df.copy()
    df["map_id"]   = df["map_id"].astype(str)
    df["event"]    = df["event"].astype(str)
    df["match_id"] = df["match_id"].astype(str)
    df["ts_dt"]    = _parse_ts(df)
    df["date"]     = df["ts_dt"].dt.date

    # ── Sidebar ──────────────────────────────────────────────────────────
    map_name = st.sidebar.selectbox("Map", list(MAP_CONFIGS.keys()))
    df_map   = df[df["map_id"] == map_name]

    dates = sorted(d for d in df_map["date"].dropna().unique())
    if dates:
        rng = st.sidebar.date_input("Date filter", value=(dates[0], dates[-1]))
        s, e = (rng[0], rng[1]) if isinstance(rng, tuple) and len(rng) == 2 else (rng, rng)
        df_map = df_map[df_map["date"].between(s, e)]

    q = st.sidebar.text_input("Match filter (substring)")
    if q.strip():
        df_map = df_map[df_map["match_id"].str.contains(q.strip(), case=False, na=False)]

    heatmap_mode = st.sidebar.toggle("Heatmap mode", False)
    bins         = st.sidebar.slider("Heatmap bins",        20, 120,   70,    5)
    max_pts      = st.sidebar.slider("Max scatter points", 2000, 50000, 20000, 1000)
    # ─────────────────────────────────────────────────────────────────────

    st.write(f"Rows after filters: `{len(df_map):,}`")

    cfg    = MAP_CONFIGS[map_name]
    df_map = _to_pixels(df_map, scale=cfg["scale"],
                        origin_x=cfg["origin_x"], origin_z=cfg["origin_z"])
    df_map = df_map[df_map["pixel_x"].between(0, IMG_SIZE) &
                    df_map["pixel_y"].between(0, IMG_SIZE)]

    fig = build_figure(df_map, map_name,
                       heatmap_mode=heatmap_mode, bins=bins, max_points=max_pts)
    st.plotly_chart(fig, use_container_width=False)


if __name__ == "__main__":
    main()