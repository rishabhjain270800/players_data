# LILA BLACK — Player Journey Visualization Tool

A browser-based tool for Level Designers to explore player behaviour across LILA BLACK's 3 maps using 5 days of production gameplay data.

🔗 **Live Tool:** https://players-data-rishabhjain.streamlit.app/

---

## What It Does

- Displays player events (kills, deaths, loot, storm deaths) as dots on the actual game minimap
- Distinguishes human players from bots visually
- Supports filtering by map, date range, and match ID
- Features a unified tab interface to seamlessly switch between Event Overviews and specialized Heatmaps (Kill Zones, Death Zones, High Traffic)
- Dynamic Live Map legend automatically updates based on the active heatmap view
- Works directly in the browser — no installation needed

---

## Running Locally

### Requirements
- Python 3.9+
- pip

### Setup

**Step 1 — Clone the repo:**
```bash
git clone https://github.com/rishabhjain270800/players_data.git
cd players_data
```

**Step 2 — Install dependencies:**
```bash
pip install -r requirements.txt
```

**Step 3 — Run the app:**
```bash
streamlit run app.py
```

**Step 4 — Open in browser:**
```
http://localhost:8501
```

---

## Folder Structure

```
players_data/
├── app.py                  ← Main Streamlit application
├── all_events.csv          ← Pre-processed event data (all 5 days)
├── parquet_to_excel_csv.py ← Script to regenerate CSV from raw parquet files
├── requirements.txt        ← Python dependencies
├── minimaps/
│   ├── AmbroseValley_Minimap.png
│   ├── GrandRift_Minimap.png
│   └── Lockdown_Minimap.jpg
├── February_10/            ← Raw parquet files (daily folders)
├── February_11/
├── February_12/
├── February_13/
└── February_14/
```

---

## Regenerating the CSV

If you want to rebuild `all_events.csv` from the raw parquet files:

```bash
python parquet_to_excel_csv.py
```

This reads all parquet files from the daily folders, decodes the event column, detects human vs bot players, and outputs `all_events.csv`.

---

## Dependencies

```
streamlit
plotly
pandas
pillow
numpy
pyarrow
```

---

## Notes

- February 14 is a partial day (data collection was still ongoing)
- The `ts` column represents match-relative time, not wall-clock time — the date filter may show a limited range
- Position/BotPosition events (movement tracking) are included in the data but filtered out from visualisation to focus on combat and loot events
