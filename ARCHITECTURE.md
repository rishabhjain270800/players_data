# Architecture — LILA BLACK Map Viewer

## What I Built
A browser-based player journey visualization tool that lets Level Designers explore 5 days of production gameplay data from LILA BLACK across 3 maps. Live at: https://players-data-rishabhjain.streamlit.app/

---

## Tech Stack & Why

| Layer | Tool | Reason |
|---|---|---|
| Frontend + Backend | Streamlit | Single Python file deploys as a full web app — no separate frontend needed |
| Charts & Map | Plotly (`go.Image` + `Scattergl`) | `go.Image` renders the minimap as a native trace; `Scattergl` handles 20k+ points smoothly via WebGL |
| Data processing | Pandas | Fast filtering, grouping, and coordinate math on 89k rows |
| Image handling | Pillow + NumPy | Converts minimap PNGs to RGBA arrays for Plotly rendering |
| Hosting | Streamlit Community Cloud | Free, deploys directly from GitHub in minutes |

---

## Data Flow

```
Parquet files (1,243 files across 5 days)
        ↓
Python script (parquet_to_excel_csv.py)
  - Reads all parquet files using pyarrow
  - Decodes event column from bytes → string
  - Detects human vs bot from user_id
  - Concatenates into one DataFrame
        ↓
all_events.csv (single flat file, ~13MB)
        ↓
User (Uploads CSV or XLSX file via sidebar)
        ↓
Streamlit app (app.py)
  - Blocks render with an elegantly styled Empty State until file is provided
  - Parses uploaded CSV/XLSX memory buffer
  - Applies sidebar filters (map, date, match)
  - Converts world coordinates → pixel coordinates
  - Renders minimap image + event dots/heatmaps via Plotly
        ↓
Browser (Level Designer sees the map)
```

---

## Coordinate Mapping Approach

The game uses a 3D world coordinate system `(x, y, z)` where `y` is elevation. For 2D minimap plotting, only `x` and `z` are used.

Each map has a known `scale` and `origin (origin_x, origin_z)`. The conversion formula:

```
u = (x - origin_x) / scale
v = (z - origin_z) / scale

pixel_x = u * 1024
pixel_y = (1 - v) * 1024     ← Y is flipped (image origin is top-left)
```

| Map | Scale | Origin X | Origin Z |
|---|---|---|---|
| AmbroseValley | 900 | -370 | -473 |
| GrandRift | 581 | -290 | -290 |
| Lockdown | 1000 | -500 | -500 |

The Y-flip was the key insight — without it, all points appear upside-down on the minimap.

---

## Assumptions Made

| Situation | Assumption |
|---|---|
| `ts` column stores match-relative time, not wall-clock | Treated as milliseconds since epoch for ordering; date filter works on the parsed date |
| Bot detection | UUID format = human, short numeric ID = bot (as per README) |
| February 14 partial day | Included as-is; noted in README |
| Events outside map bounds | Clipped to 0–1024 pixel range and excluded |

---

## Trade-offs

| Decision | Chose | Considered | Why |
|---|---|---|---|
| Data format | Pre-process to CSV | Query parquet live | CSV loads instantly in browser; parquet adds complexity |
| Rendering | Plotly Scattergl | Leaflet.js + React | Streamlit-native, no separate frontend needed |
| Image rendering | `go.Image` trace | `add_layout_image` | Layout images failed silently in some Plotly versions |
| Heatmaps | `go.Histogram2d` | `Densitymapbox` | Can be directly overlaid on `go.Image` with `zsmooth="best"` and custom colorscale for highly prominent density maps |
| UI Layout | Native `st.tabs` | Custom HTML & CSS | Provides robust, clickable navigation headers that natively trigger Python reruns without CSS hacks |
| Hosting | Streamlit Cloud | Vercel + FastAPI | Single-service deployment, no backend needed |

---

## What I'd Do With More Time

- **Robust Backend Database:** Migrate the data layer from a heavy memory-mapped CSV file into an active SQL backend (e.g., PostgreSQL or ClickHouse) to allow instantaneous performance scaling for millions of matches.
- **3D Topography Elevation:** Implement true 3D map plotting where events are elevated according to their exact coordinate verticality, giving Level Designers deep structural insights.
- **Advanced Path Clustering:** Build a machine learning clustering overlay that automatically highlights anomalous player paths to instantly catch bug abusers or map terrain exploits.
- **Authentication & Security:** Wrap the application architecture seamlessly behind a robust OAuth wall so proprietary raw match data is fully protected from public access.
- Add **GeoJSON-style zone overlays** for storm boundaries per timestamp
