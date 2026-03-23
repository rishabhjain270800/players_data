import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from PIL import Image

# ── Constants ────────────────────────────────────────────────────────────────

MAP_CONFIGS = {
    "Lockdown":      {"scale": 1000, "origin_x": -500, "origin_z": -500,
                      "image": "Lockdown_Minimap.jpg",      "display": "LOCKDOWN"},
    "GrandRift":     {"scale": 581,  "origin_x": -290, "origin_z": -290,
                      "image": "GrandRift_Minimap.png",     "display": "GRANDRIFT"},
    "AmbroseValley": {"scale": 900,  "origin_x": -370, "origin_z": -473,
                      "image": "AmbroseValley_Minimap.png", "display": "AMBROSEVALLEY"},
}

KILL_EVENTS  = {"Kill", "BotKill"}
DEATH_EVENTS = {"Killed", "BotKilled"}
LOOT_EVENTS  = {"Loot"}
STORM_EVENTS = {"KilledByStorm"}

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
IMG_SIZE   = 1024
MAX_POINTS = 25000


# ── CSS ──────────────────────────────────────────────────────────────────────

def inject_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    html, body, [class*="css"], .stApp {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #0A0C14 !important;
        color: #FFFFFF;
    }

    /* Hide default Streamlit elements */
    #MainMenu, footer, header { visibility: hidden; }
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }

    /* ── TOP NAVBAR ── */
    .top-navbar {
        background: #0D0F1A;
        border-bottom: 1px solid #1E2235;
        padding: 0 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        height: 56px;
        position: sticky;
        top: 0;
        z-index: 999;
    }
    .navbar-logo {
        font-size: 1rem;
        font-weight: 900;
        letter-spacing: 0.05em;
        color: #FFFFFF;
    }
    .navbar-logo span { color: #FF3B30; }
    .navbar-subtitle {
        font-size: 0.6rem;
        color: #8B8FA8;
        letter-spacing: 0.12em;
        margin-top: 1px;
    }
    .navbar-tabs {
        display: flex;
        gap: 32px;
        align-items: center;
    }
    .navbar-tab {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        color: #8B8FA8;
        cursor: pointer;
        padding: 18px 0;
        border-bottom: 2px solid transparent;
        text-transform: uppercase;
    }
    .navbar-tab.active {
        color: #FF3B30;
        border-bottom: 2px solid #FF3B30;
    }
    .navbar-icons { display: flex; gap: 16px; align-items: center; }
    .navbar-icon {
        width: 32px; height: 32px;
        background: #1E2235;
        border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.85rem; cursor: pointer;
        border: 1px solid #2A2D3E;
    }

    /* ── SIDEBAR ── */
    [data-testid="stSidebar"] {
        background-color: #0D0F1A !important;
        border-right: 1px solid #1E2235 !important;
        min-width: 220px !important;
        max-width: 220px !important;
    }
    [data-testid="stSidebar"] > div {
        padding: 20px 16px !important;
    }
    [data-testid="stSidebar"] * { color: #FFFFFF !important; }

    /* ── SIDEBAR EXPLORER HEADER ── */
    .sidebar-header {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 20px;
    }
    .sidebar-icon {
        width: 28px; height: 28px;
        background: #FF3B30;
        border-radius: 6px;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.9rem;
    }
    .sidebar-title {
        font-size: 0.85rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
    }

    /* ── WIDGET THEME FIXES ── */
    div[data-testid="stFileUploader"] > section {
        background-color: #0D0F1A !important;
        border: 1px dashed #2A2D3E !important;
    }
    div[data-testid="stFileUploader"] span, div[data-testid="stFileUploader"] p {
        color: #8B8FA8 !important;
    }
    /* Fix file uploader button explicitly so text is visible */
    div[data-testid="stFileUploader"] button {
        background-color: #1E2235 !important;
        border: 1px solid #2A2D3E !important;
    }
    div[data-testid="stFileUploader"] button span {
        color: #FFFFFF !important;
    }
    
    div[data-testid="stDateInput"] input, div[data-baseweb="select"] > div {
        background-color: #0D0F1A !important;
        color: #FFFFFF !important;
        border: 1px solid #1E2235 !important;
    }
    div[data-baseweb="popover"], div[data-baseweb="menu"] {
        background-color: #0D0F1A !important;
        border: 1px solid #1E2235 !important;
    }
    ul[role="listbox"] li {
        background-color: transparent !important;
        color: #FFFFFF !important;
    }
    ul[role="listbox"] li:hover {
        background-color: #1E2235 !important;
    }

    /* ── SIDEBAR SELECTIONS ── */
    [data-testid="stSidebar"] .stButton {
        margin-bottom: 8px;
    }
    [data-testid="stSidebar"] .stButton > button {
        display: block !important;
        width: 100% !important;
        height: auto !important;
        text-align: left !important;
        padding: 12px 14px !important;
        border-radius: 4px !important;
        border: 1px solid #1E2235 !important;
        background: #0D0F1A !important;
        color: #FFFFFF !important;
        cursor: pointer !important;
        font-weight: 700 !important;
        letter-spacing: 0.05em !important;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #1E2235 !important;
    }
    
    /* Active tab overrides */
    button[data-baseweb="tab"] {
        background-color: transparent !important;
    }
    button[data-baseweb="tab"] p {
        font-size: 0.72rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.1em !important;
        text-transform: uppercase !important;
        color: #8B8FA8 !important;
    }
    button[aria-selected="true"] p {
        color: #FF3B30 !important;
    }
    div[data-baseweb="tab-highlight"] {
        background-color: #FF3B30 !important;
    }

    /* ── SIDEBAR SECTION LABELS ── */
    .sb-label {
        font-size: 0.6rem;
        font-weight: 700;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: #8B8FA8;
        margin-top: 18px;
        margin-bottom: 8px;
    }

    /* ── VIEW MODE PILLS ── */
    .pill-row { display: flex; gap: 8px; margin-top: 4px; }
    .pill {
        flex: 1;
        padding: 7px 10px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.06em;
        text-align: center;
        cursor: pointer;
        border: 1px solid #2A2D3E;
        background: #1A1D2E;
        color: #8B8FA8;
        text-transform: uppercase;
    }
    .pill.active {
        background: #FF3B30;
        border-color: #FF3B30;
        color: #FFFFFF;
    }

    /* ── EXPORT BUTTON ── */
    .export-btn {
        width: 100%;
        padding: 12px;
        background: #FF3B30;
        color: #FFFFFF;
        border: none;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        cursor: pointer;
        margin-top: 24px;
        text-align: center;
    }

    /* ── STAT CARDS ── */
    .stat-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 12px;
        margin: 16px 0;
    }
    .stat-card {
        background: #0D0F1A;
        border: 1px solid #1E2235;
        border-radius: 4px;
        padding: 16px 20px;
    }
    .stat-label {
        font-size: 0.6rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #8B8FA8;
        margin-bottom: 8px;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: 800;
        color: #FFFFFF;
        line-height: 1;
    }



    /* ── MAP CONTAINER ── */
    .map-container {
        background: #0D0F1A;
        border: 1px solid #1E2235;
        border-top: none;
        border-radius: 0 0 4px 4px;
        padding: 0;
        overflow: hidden;
        position: relative;
    }

    /* ── LIVE LEGEND ── */
    .live-legend {
        position: absolute;
        bottom: 20px;
        right: 20px;
        background: rgba(13,15,26,0.9);
        border: 1px solid #2A2D3E;
        border-radius: 4px;
        padding: 12px 16px;
        z-index: 10;
    }
    .legend-title {
        font-size: 0.55rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #8B8FA8;
        margin-bottom: 8px;
    }
    .legend-item {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 0.7rem;
        font-weight: 600;
        letter-spacing: 0.06em;
        text-transform: uppercase;
        color: #FFFFFF;
        margin-bottom: 4px;
    }
    .legend-dot {
        width: 8px; height: 8px;
        border-radius: 50%;
    }

    /* ── INSIGHT CARDS ── */
    .insight-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 12px;
        margin-top: 16px;
    }
    .insight-card {
        background: #0D0F1A;
        border: 1px solid #1E2235;
        border-radius: 4px;
        padding: 20px;
    }
    .insight-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 12px;
    }
    .insight-icon-wrap {
        width: 36px; height: 36px;
        background: #1E2235;
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.1rem;
    }
    .insight-category {
        font-size: 0.58rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #8B8FA8;
    }
    .insight-title {
        font-size: 0.95rem;
        font-weight: 700;
        color: #FFFFFF;
        margin-bottom: 6px;
    }
    .insight-stat {
        font-size: 1.4rem;
        font-weight: 900;
        margin-bottom: 8px;
        line-height: 1.1;
    }
    .insight-stat.red    { color: #FF3B30; }
    .insight-stat.yellow { color: #FFD400; }
    .insight-stat.blue   { color: #4A90FF; }
    .insight-body {
        font-size: 0.72rem;
        color: #8B8FA8;
        line-height: 1.5;
    }
    .insight-body b { color: #FFFFFF; }

    /* ── TIMELINE PANEL ── */
    .timeline-wrap {
        background: #0D0F1A;
        border: 1px solid #1E2235;
        border-radius: 4px;
        padding: 14px 18px;
        margin-bottom: 12px;
    }
    .timeline-head {
        font-size: 0.65rem;
        font-weight: 700;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: #FF3B30;
        margin-bottom: 4px;
    }
    .timeline-sub {
        font-size: 0.7rem;
        color: #8B8FA8;
        margin-bottom: 10px;
    }

    /* Streamlit widget cleanup */
    .stRadio > div { gap: 6px !important; }
    .stCheckbox > label > div { gap: 8px !important; }
    div[data-testid="stCheckbox"] label { font-size: 0.8rem !important; }
    .stSelectbox label { font-size: 0.7rem !important; }
    .stSlider { padding: 0 !important; }
    div[data-testid="stButton"] button.export-btn {
        background: #FF3B30 !important;
        color: white !important;
        border: none !important;
        border-radius: 4px !important;
        font-weight: 700 !important;
        letter-spacing: 0.06em !important;
        font-size: 0.75rem !important;
    }
    </style>
    """, unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

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


def _is_human(s):
    return s.astype(str).map(lambda v: bool(UUID_RE.match(v)))


def _to_pixels(df, *, scale, origin_x, origin_z):
    df = df.copy()
    df["x"] = pd.to_numeric(df["x"], errors="coerce")
    df["z"] = pd.to_numeric(df["z"], errors="coerce")
    df["pixel_x"] = ((df["x"] - origin_x) / scale) * IMG_SIZE
    df["pixel_y"] = (1.0 - ((df["z"] - origin_z) / scale)) * IMG_SIZE
    return df


def _load_map_image(map_name):
    p = Path(__file__).resolve().parent / "minimaps" / MAP_CONFIGS[map_name]["image"]
    if not p.exists():
        return None
    return np.array(Image.open(p).convert("RGBA").resize((IMG_SIZE, IMG_SIZE)))


def _hex_rgba(h, a):
    h = h.lstrip("#")
    r, g, b = int(h[0:2],16), int(h[2:4],16), int(h[4:6],16)
    return f"rgba({r},{g},{b},{a})"


def _map_zone(px, py):
    return ("N" if py < IMG_SIZE/2 else "S") + ("W" if px < IMG_SIZE/2 else "E")


def fmt_s(s):
    s = int(s)
    return f"{s//60:02d}:{s%60:02d}"


# ── Figure ────────────────────────────────────────────────────────────────────

def build_figure(df_map, map_name, *, mode, show_kills, show_deaths,
                 show_loot, show_storm, player_filter):

    fig = go.Figure()
    img = _load_map_image(map_name)
    if img is not None:
        fig.add_trace(go.Image(z=img))
        fig.update_xaxes(range=[-0.5, IMG_SIZE-0.5])
        fig.update_yaxes(range=[IMG_SIZE-0.5, -0.5])
    else:
        fig.update_xaxes(range=[0, IMG_SIZE])
        fig.update_yaxes(range=[IMG_SIZE, 0])

    fig.update_layout(
        height=620, width=None,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="#0D0F1A",
        plot_bgcolor="#0D0F1A",
        showlegend=False,
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=""),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False, title=""),
    )

    if df_map.empty:
        return fig

    df_map = df_map.dropna(subset=["pixel_x","pixel_y","event","user_id"]).copy()
    df_map["is_human"] = _is_human(df_map["user_id"])

    if player_filter == "Humans Only":
        df_map = df_map[df_map["is_human"]]
    elif player_filter == "Bots Only":
        df_map = df_map[~df_map["is_human"]]

    layers = []
    if show_kills:  layers.append(("Player Kills", {"Kill","BotKill"},   "#FF3B30"))
    if show_deaths: layers.append(("Fatalities",   {"Killed","BotKilled"},"#4A90FF"))
    if show_loot:   layers.append(("Elite Loot",   {"Loot"},              "#34C759"))
    if show_storm:  layers.append(("Storm Death",  {"KilledByStorm"},     "#FFD400"))

    # heatmap modes
    if mode in ("Kill Zones", "Death Zones", "High Traffic"):
        if mode == "Kill Zones":
            h_layers = [l for l in layers if l[0] == "Player Kills"]
        elif mode == "Death Zones":
            h_layers = [l for l in layers if l[0] == "Fatalities"]
        else:
            h_layers = layers
        for label, events, color in h_layers:
            df_e = df_map[df_map["event"].isin(events)]
            if df_e.empty: continue
            fig.add_trace(go.Histogram2d(
                x=df_e["pixel_x"], y=df_e["pixel_y"],
                nbinsx=100, nbinsy=100, zmin=0,
                colorscale=[
                    [0.0, "rgba(0,0,0,0)"],
                    [0.05, _hex_rgba(color, 0.5)],
                    [0.3, _hex_rgba(color, 0.8)],
                    [1.0, _hex_rgba(color, 1.0)]
                ],
                zsmooth="best",
                showscale=False, name=label,
            ))
    else:
        # scatter
        if len(df_map) > MAX_POINTS:
            df_map = df_map.sample(n=MAX_POINTS, random_state=42)
        for label, events, color in layers:
            df_e = df_map[df_map["event"].isin(events)]
            if df_e.empty: continue
            
            # Make storm dots larger and more prominent
            if label == "Storm Death":
                line_dict = dict(width=1.5, color='white')
                sz_human = 14
                sz_bot = 12
            else:
                line_dict = None
                sz_human = 8
                sz_bot = 6
                
            for grp, mask, sym, sz in [
                ("Player", df_e["is_human"],  "circle",  sz_human),
                ("Bot",   ~df_e["is_human"],  "diamond", sz_bot),
            ]:
                df_g = df_e[mask]
                if df_g.empty: continue
                fig.add_trace(go.Scattergl(
                    x=df_g["pixel_x"], y=df_g["pixel_y"],
                    mode="markers",
                    marker=dict(size=sz, color=color, symbol=sym, opacity=0.85 if label != "Storm Death" else 1.0, line=line_dict),
                    name=f"{label} ({grp})",
                    hovertemplate=f"<b>{label}</b> ({grp})<br>Match: %{{customdata}}<extra></extra>",
                    customdata=df_g["match_id"].values,
                ))
    return fig


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="LILA BLACK — Map Intelligence",
        page_icon="🎮", layout="wide",
    )
    inject_css()

    # ── TOP NAVBAR ───────────────────────────────────────────────────────
    st.markdown("""
    <div class="top-navbar">
        <div>
            <div class="navbar-logo">LILA <span>BLACK</span> — MAP INTELLIGENCE</div>
            <div class="navbar-subtitle">UNDERSTAND WHERE PLAYERS FIGHT, DIE, LOOT AND GET CAUGHT BY THE STORM</div>
        </div>
        <div class="navbar-tabs">
            <div class="navbar-tab active">Map Explorer</div>
        </div>
        <div class="navbar-icons">
            <div class="navbar-icon">⚙️</div>
            <div class="navbar-icon">❓</div>
            <div class="navbar-icon">👤</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── LOAD DATA ────────────────────────────────────────────────────────
    base_dir    = Path(__file__).resolve().parent
    default_csv = base_dir / "all_events.csv"

    with st.sidebar:
        # Upload option
        st.markdown("""
        <div class="sidebar-header">
            <div class="sidebar-icon">🗺</div>
            <div class="sidebar-title">Explorer</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown('<div class="sb-label">📂 Data Source</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("", type=["csv"], label_visibility="collapsed")
        if uploaded:
            st.success(f"✅ {uploaded.name}")

    if uploaded:
        df = pd.read_csv(uploaded, low_memory=False)
    elif default_csv.exists():
        df = pd.read_csv(default_csv, low_memory=False)
    else:
        st.error("❌ No data found. Place `all_events.csv` next to `app.py` or upload one.")
        st.stop()

    df = df.copy()
    df["map_id"]   = df["map_id"].astype(str)
    df["event"]    = df["event"].astype(str)
    df["match_id"] = df["match_id"].astype(str)
    df["ts_dt"]    = _parse_ts(df)
    df["date"]     = df["ts_dt"].dt.date
    df["is_human"] = _is_human(df["user_id"])

    # ── SIDEBAR FILTERS ──────────────────────────────────────────────────
    with st.sidebar:

        # Map selection
        st.markdown('<div class="sb-label">Map Selection</div>', unsafe_allow_html=True)
        map_counts = df.groupby("map_id")["match_id"].nunique().to_dict()
        if "sel_map" not in st.session_state:
            st.session_state.sel_map = "Lockdown"

        for mk, cfg in MAP_CONFIGS.items():
            cnt = map_counts.get(mk, 0)
            btn_label = f"{cfg['display']} ({cnt:,} Matches)"
            
            # Show which map is active via label prefix instead of complex CSS injections
            if st.session_state.sel_map == mk:
                btn_label = f"📍 " + btn_label
            
            if st.button(btn_label, key=f"mbtn_{mk}", use_container_width=True):
                st.session_state.sel_map = mk
                st.rerun()

        map_name = st.session_state.sel_map
        df_map   = df[df["map_id"] == map_name].copy()

        # Timeframe
        st.markdown('<div class="sb-label">Timeframe</div>', unsafe_allow_html=True)
        dates = sorted(d for d in df_map["date"].dropna().unique())
        if dates:
            rng = st.date_input("", value=(dates[0], dates[-1]),
                                label_visibility="collapsed")
            s, e = (rng[0], rng[1]) if isinstance(rng, tuple) and len(rng)==2 \
                   else (rng, rng)
            df_map = df_map[df_map["date"].between(s, e)]

        # Match filter
        st.markdown('<div class="sb-label">Match Filter</div>', unsafe_allow_html=True)
        pcounts  = df_map.groupby("match_id")["user_id"].nunique().to_dict()
        m_opts   = ["All Matches"] + [f"{m[:8]}... ({pcounts.get(m,0)} players)"
                                       for m in sorted(pcounts)]
        m_ids    = [None] + sorted(pcounts)
        sel_mlbl = st.selectbox("", m_opts, label_visibility="collapsed")
        sel_mid  = m_ids[m_opts.index(sel_mlbl)]
        if sel_mid:
            df_map = df_map[df_map["match_id"] == sel_mid]



        # Show Events
        st.markdown('<div class="sb-label">Show Events</div>', unsafe_allow_html=True)
        show_kills  = st.checkbox("🔴 Kills",        value=True)
        show_deaths = st.checkbox("🔵 Deaths",       value=True)
        show_loot   = st.checkbox("🟢 Loot Drops",   value=True)
        show_storm  = st.checkbox("🟡 Storm Deaths", value=True)

        # Player type
        st.markdown('<div class="sb-label">Player Type</div>', unsafe_allow_html=True)
        p_filter = st.radio("", ["All Players", "Humans Only", "Bots Only"],
                            label_visibility="collapsed")

        # Export button
        st.markdown('<div class="export-btn">⬇ EXPORT INTELLIGENCE</div>',
                    unsafe_allow_html=True)

    # ── STAT CARDS ───────────────────────────────────────────────────────
    df_f         = df_map.copy()
    tot_matches  = df_f["match_id"].nunique()
    tot_kills    = df_f[df_f["event"].isin(KILL_EVENTS)].shape[0]
    tot_deaths   = df_f[df_f["event"].isin(DEATH_EVENTS)].shape[0]
    storm_deaths = df_f[df_f["event"].isin(STORM_EVENTS)].shape[0]
    all_deaths   = tot_deaths + storm_deaths
    storm_rate   = round(storm_deaths / all_deaths * 100, 1) if all_deaths else 0

    st.markdown(f"""
    <div class="stat-grid" style="padding:16px 24px 0 24px;">
        <div class="stat-card">
            <div class="stat-label">Total Matches</div>
            <div class="stat-value">{tot_matches:,}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Total Kills</div>
            <div class="stat-value">{tot_kills:,}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Total Deaths</div>
            <div class="stat-value">{tot_deaths:,}</div>
        </div>
        <div class="stat-card">
            <div class="stat-label">Storm Kill Rate</div>
            <div class="stat-value">{storm_rate}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── TAB BAR & CONTENT ────────────────────────────────────────────────
    st.markdown('<div style="padding:0 24px;">', unsafe_allow_html=True)
    
    # Define available tabs
    tab_opts = ["Events Overview", "Kill Zones", "Death Zones", "High Traffic"]

    # Use native Streamlit tabs wrapped in our styling
    st_tabs = st.tabs(tab_opts)
    
    for i, t in enumerate(tab_opts):
        with st_tabs[i]:
            # Determine logic mode corresponding to this tab
            render_mode = "scatter" if t == "Events Overview" else t
            
            # Fetch data for this map
            cfg   = MAP_CONFIGS[map_name]
            df_px = _to_pixels(df_map, scale=cfg["scale"],
                               origin_x=cfg["origin_x"], origin_z=cfg["origin_z"])
            df_px = df_px[df_px["pixel_x"].between(0, IMG_SIZE) &
                          df_px["pixel_y"].between(0, IMG_SIZE)]
            
            # Build the figure independently for the active tab
            fig = build_figure(df_px, map_name, mode=render_mode,
                               show_kills=show_kills, show_deaths=show_deaths,
                               show_loot=show_loot, show_storm=show_storm,
                               player_filter=p_filter)
                               
            # Render layout
            map_col, leg_col = st.columns([10, 1])
            with map_col:
                st.plotly_chart(fig, use_container_width=True, key=f"plot_{t}_{map_name}")
            
            # Floating legend (dynamic HTML below map)
            active_events = []
            if render_mode == "scatter" or render_mode == "High Traffic":
                if show_kills:  active_events.append(("Player Kills", "#FF3B30"))
                if show_deaths: active_events.append(("Fatalities",   "#4A90FF"))
                if show_loot:   active_events.append(("Elite Loot",   "#34C759"))
                if show_storm:  active_events.append(("Storm Death",  "#FFD400"))
            elif render_mode == "Kill Zones":
                if show_kills:  active_events.append(("Player Kills", "#FF3B30"))
            elif render_mode == "Death Zones":
                if show_deaths: active_events.append(("Fatalities",   "#4A90FF"))

            if active_events:
                leg_html = """
                <div style="display:flex;justify-content:flex-end;margin-top:-60px;
                            padding-right:30px;position:relative;z-index:10;">
                    <div class="live-legend">
                        <div class="legend-title">Live Map Legend</div>
                """
                for name, clr in active_events:
                    leg_html += f'<div class="legend-item"><div class="legend-dot" style="background:{clr}"></div> {name}</div>\n'
                leg_html += "</div></div>"
                st.markdown(leg_html, unsafe_allow_html=True)
            
            # Timeline & Insights layout
            st.markdown('<hr style="border-color:#1E2235;margin:24px 0;">', unsafe_allow_html=True)
            
            # Timeline
            if sel_mid:
                df_tl = df_map.dropna(subset=["ts_dt"]).copy()
                if not df_tl.empty:
                    t0 = df_tl["ts_dt"].min()
                    t1 = df_tl["ts_dt"].max()
                    total_secs = max(int((t1-t0).total_seconds()), 1)
                    df_tl["match_sec"] = ((df_tl["ts_dt"]-t0).dt.total_seconds()).astype(int)

                    if "tl_val" not in st.session_state:
                         st.session_state["tl_val"] = 100

                    st.markdown("""
                    <div class="timeline-wrap">
                        <div class="timeline-head">⏱ Match Playback</div>
                        <div class="timeline-sub">Timeline specific to selected match.</div>
                    </div>
                    """, unsafe_allow_html=True)

                    tl1, tl2 = st.columns([5, 1])
                    with tl1:
                        pct = st.slider("", 0, 100, value=st.session_state["tl_val"], 
                                        step=1, label_visibility="collapsed", key=f"slider_{t}")
                    with tl2:
                        cut = int(pct / 100 * total_secs)
                        st.markdown(f'<div style="padding-top:6px;color:#FF3B30;font-weight:700;">{fmt_s(cut)} / {fmt_s(total_secs)}</div>', unsafe_allow_html=True)
            else:
                st.markdown("""
                <div style="background:#0D0F1A;border:1px solid #1E2235;border-left:3px solid #FF3B30;
                            border-radius:4px;padding:10px 16px;margin-bottom:20px;">
                    <span style="color:#FF3B30;font-weight:700;font-size:0.75rem;">⏱ MATCH PLAYBACK</span>
                    <span style="color:#8B8FA8;font-size:0.75rem;margin-left:10px;">Select a specific match to enable playback.</span>
                </div>
                """, unsafe_allow_html=True)

            # Insights
            df_k = df_px[df_px["event"].isin(KILL_EVENTS)].copy()
            if not df_k.empty:
                df_k["zone"] = df_k.apply(lambda r: _map_zone(r["pixel_x"],r["pixel_y"]),axis=1)
                zc   = df_k["zone"].value_counts()
                tzn  = {"NW":"NW QUARTER","NE":"NE QUARTER",
                        "SW":"SW QUARTER","SE":"SE QUARTER"}.get(zc.index[0],"N/A")
                tzcnt = zc.iloc[0]
            else:
                tzn, tzcnt = "N/A", 0

            s_pct   = round(storm_deaths/all_deaths*100,1) if all_deaths else 0
            one_in  = round(all_deaths/storm_deaths) if storm_deaths else 0
            bk      = df_f[df_f["event"]=="BotKill"].shape[0]
            hk      = df_f[df_f["event"]=="Kill"].shape[0]
            ratio   = f"{round(bk/hk,1)}:1 K/D RATIO" if hk else "N/A"
            r_ctx   = f"Bots are engaging players effectively on {MAP_CONFIGS[map_name]['display'].title()}."

            st.markdown(f"""
            <div class="insight-grid">
                <div class="insight-card">
                    <div class="insight-header">
                        <div class="insight-icon-wrap">🎯</div>
                        <div class="insight-category">Hotspot Analysis</div>
                    </div>
                    <div class="insight-title">Most Contested Zone</div>
                    <div class="insight-stat red">{tzn}</div>
                    <div class="insight-body">Recorded <b>{tzcnt:,} Kills</b> in this zone.</div>
                </div>
                <div class="insight-card">
                    <div class="insight-header">
                        <div class="insight-icon-wrap">⛈️</div>
                        <div class="insight-category">Environmental Risk</div>
                    </div>
                    <div class="insight-title">Storm Danger Rate</div>
                    <div class="insight-stat yellow">{s_pct}% FATALITY</div>
                    <div class="insight-body">1 in {one_in} players fail to outrun the storm phase.</div>
                </div>
                <div class="insight-card">
                    <div class="insight-header">
                        <div class="insight-icon-wrap">🤖</div>
                        <div class="insight-category">Combat Balance</div>
                    </div>
                    <div class="insight-title">Bot vs Human Combat</div>
                    <div class="insight-stat blue">{ratio}</div>
                    <div class="insight-body">{r_ctx}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()