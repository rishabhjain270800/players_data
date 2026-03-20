# Player Behaviour Insights — LILA BLACK

*Derived from 5 days of production data (Feb 10–14, 2026) using the LILA BLACK Map Viewer tool.*

---

## Insight 1: AmbroseValley Has a Dominant "Death Corridor" in the Centre

**What I noticed:**
When viewing AmbroseValley in heatmap mode with Deaths selected, there is a clear high-density cluster of kills and deaths in the central area of the map (roughly pixel range 400–600 on both axes). This zone consistently shows the highest concentration of red (kills) and blue (deaths) markers across all 5 days of data.

**Evidence:**
- Over 61,000 events are recorded on AmbroseValley — the most played map by far
- The central cluster contains approximately 3–4x more kill/death events than any other zone
- The same hotspot appears consistently across different matches and different days, confirming it is structural (map design driven) rather than coincidental

**Actionable Recommendation:**
- The central corridor is likely a chokepoint — players are funnelled through it due to terrain or building layout
- Level designers should consider adding alternative routes around this area to reduce predictable combat and encourage more varied player movement
- Metrics to track: kill-to-death ratio in central zone vs. other zones, average match survival time for players who pass through vs. avoid this area

**Why a Level Designer should care:**
If all fights happen in one place, the rest of the map becomes irrelevant. Distributing combat more evenly across the map increases replayability and makes the full map investment worthwhile.

---

## Insight 2: Storm Deaths Are Concentrated at Map Edges — Players Are Getting Caught Off-Guard

**What I noticed:**
`KilledByStorm` events (yellow markers) consistently appear at the outer edges and corners of all 3 maps, rather than being spread evenly. This suggests players are frequently failing to extract or rotate in time before the storm reaches them.

**Evidence:**
- Storm death markers cluster heavily near the map boundaries on AmbroseValley and GrandRift
- Storm deaths represent a notable share of total deaths — they are not rare edge-case events
- The pattern repeats across multiple days, suggesting it is a systemic issue rather than isolated player error

**Actionable Recommendation:**
- The storm may be moving too fast in the early zones, not giving players enough time to react and rotate
- Consider adding clearer in-game storm warning indicators, or slightly slowing the storm's initial push speed
- Alternatively, add more loot or objectives in the inner safe zone to incentivise players to move inward earlier
- Metrics to track: average time between storm warning and player death, storm death rate by map zone

**Why a Level Designer should care:**
High storm death rates at map edges suggest the storm pacing or map layout is punishing players unfairly. Deaths to the environment rather than other players reduce the feeling of agency and can frustrate new players.

---

## Insight 3: GrandRift and Lockdown Are Significantly Under-Played Compared to AmbroseValley

**What I noticed:**
When switching between maps in the tool, the row count drops dramatically. AmbroseValley shows 61,000+ events while GrandRift and Lockdown show far fewer. This means most matches are being played on AmbroseValley, leaving the other two maps largely unexplored.

**Evidence:**
- AmbroseValley: ~61,000 events (majority of all data)
- GrandRift and Lockdown: significantly lower event counts
- Loot distribution on GrandRift and Lockdown shows sparse green markers, suggesting fewer players are reaching loot locations on those maps

**Actionable Recommendation:**
- Investigate whether the map rotation system is weighted towards AmbroseValley, or whether players are actively avoiding the other maps
- Consider adding exclusive high-value loot or unique objectives to GrandRift and Lockdown to incentivise players to engage with them
- Run a limited-time event forcing Lockdown-only matches to gather more behavioural data on that map
- Metrics to track: map selection rate (if players can choose), match completion rate per map, average session length per map

**Why a Level Designer should care:**
If two out of three maps are being ignored, that represents a large investment of design and art resources going underutilised. Understanding *why* players avoid certain maps is essential for improving them or adjusting the rotation system.
