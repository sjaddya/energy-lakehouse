# SMARD API notes (step a2)

Source: Bundesnetzagentur | SMARD.de.

**Licence:** the SMARD download page states that the data provided on SMARD may be downloaded,
stored and reused free of charge under **CC BY 4.0**. Attribution used in this project:
"Data: Bundesnetzagentur | SMARD.de, CC BY 4.0". Put it in the README and in the dashboard
footer.

## URL pattern

```
index:  https://www.smard.de/app/chart_data/{filterId}/{region}/index_{resolution}.json
data:   https://www.smard.de/app/chart_data/{filterId}/{region}/{filterId}_{region}_{resolution}_{chunk}.json
```

- **filterId** — the series. The market area for prices is encoded here, not in `region`.
- **region** — `DE` for national; TSO zones (50Hertz, Amprion, TenneT, TransnetBW) use the same slot.
- **resolution** — `hour` (also quarterhour, day, week, month, year).
- **chunk** — epoch **milliseconds** of the start of a week. Hourly data is served one file per
  week, each starting **Monday 00:00 Berlin time** (verified: 1789941600000 = Mon 21.09.2026
  00:00 Berlin = 22:00 UTC Sunday; 1788127200000 = Mon 31.08.2026 00:00 Berlin).
- No API key, no cookies and no headers are required. The browser's "copy as cURL" output
  contains a personal session cookie - never paste that into the repo.

`index_{resolution}.json` lists the chunk timestamps that exist for that series.

## Confirmed filter IDs - realised generation, region DE

Verified by downloading the hourly CSV for 12.09-23.09.2026 from the SMARD download centre and
comparing every hour against the JSON for each candidate ID
(script: scratch `match_ids.py`; mean absolute difference 0.0000 unless noted).

| filterId | German name | English | Unit | Note |
|---|---|---|---|---|
| 4066 | Biomasse | Biomass | MWh | |
| 1226 | Wasserkraft | Hydro | MWh | |
| 1225 | Wind Offshore | Wind offshore | MWh | project input |
| 4067 | Wind Onshore | Wind onshore | MWh | project input |
| 4068 | Photovoltaik | Solar PV | MWh | project input; mean diff 0.21 - see revisions below |
| 1228 | Sonstige Erneuerbare | Other renewable | MWh | |
| 1224 | Kernenergie | Nuclear | MWh | **no data**: every chunk returns HTTP 404; CSV column is "-" |
| 1223 | Braunkohle | Lignite | MWh | conventional group |
| 4069 | Steinkohle | Hard coal | MWh | conventional group |
| 4071 | Erdgas | Natural gas | MWh | conventional group; mean diff 0.0004 |
| 4070 | Pumpspeicher | Pumped storage | MWh | conventional group |
| 1227 | Sonstige Konventionelle | Other conventional | MWh | conventional group |

## Confirmed filter IDs - wholesale prices (EUR/MWh), region DE

Same method, against the Grosshandelspreise CSV for 12.09-23.09.2026. All matched exactly
(0.0000 over 264 hours).

| filterId | Market area | | filterId | Market area |
|---|---|---|---|---|
| **4169** | **Deutschland/Luxemburg - the one this project uses** | | 256 | Niederlande |
| 5078 | Durchschnitt Anrainer DE/LU | | 257 | Polen |
| 4996 | Belgien | | 258 | Schweden 4 |
| 4997 | Norwegen 2 | | 259 | Schweiz |
| 4170 | Oesterreich | | 260 | Slowenien |
| 252 | Daenemark 1 | | 261 | Tschechien |
| 253 | Daenemark 2 | | 262 | Ungarn |
| 254 | Frankreich | | 255 | Italien (Nord) |

Note: 260 and 262 were captured from the browser first and are **Slovenia and Hungary**, not
Germany. Nothing in the response says so - only the value comparison does.

## Confirmed filter IDs - realised consumption (MWh), region DE

| filterId | Series | Use |
|---|---|---|
| **410** | Netzlast | **the load figure this project uses** |
| 5140 | Netzlast inkl. Pumpspeicher | grid load including pumped-storage consumption |
| 4359 | Residuallast | load minus renewables; goes negative when renewables exceed load |
| 4387 | Pumpspeicher | pumped-storage consumption only |

## The five series Project A ingests

| Purpose | filterId | Series |
|---|---|---|
| Price (y-axis, headline number) | 4169 | Day-ahead price Deutschland/Luxemburg, EUR/MWh |
| Renewable output (x-axis) | 4067 | Wind Onshore, MWh |
| Renewable output (x-axis) | 1225 | Wind Offshore, MWh |
| Renewable output (x-axis) | 4068 | Photovoltaik, MWh |
| Load (supporting view 2) | 410 | Netzlast, MWh |

Plus the conventional group (1223, 4069, 4071, 4070, 1227) and the remaining renewables
(4066, 1226, 1228) for the renewable-share denominator in supporting view 1.

## Traps found, and what they mean for the pipeline

- **Weekly chunks on Berlin midnight, timestamps in epoch ms.** Berlin observes DST, so the
  October chunk has 25 hours and one repeated local hour. Store UTC in bronze and silver;
  convert to Berlin only for display, or the "unique timestamp" test fails one day a year.
- **Missing series return HTTP 404, not an empty body** (nuclear, 1224). Ingestion must treat a
  404 chunk as "nothing published" and carry on, not as a failure to retry three times.
- **Values are revised.** Solar differed from the CSV by 0.21 MWh on average over the same hours,
  and gas by 0.0004 - the API had been updated after the CSV was produced. This is the
  justification for re-fetching the last 48 hours on every run.
- **Nulls at the end of a chunk** for hours not yet published. Null is missing, not zero.
- **CSV format from the download centre:** semicolon separated, German number format
  (dot = thousands, comma = decimal), `-` for no data, and separate "Datum von" / "Datum bis"
  columns. Only relevant for manual checks; the pipeline reads JSON.
- **Units:** generation in MWh per hour; prices in EUR/MWh; load in MWh.

## How the mapping was proved

`tools/match_ids.py` (scratch tooling, not project code):

    python tools/match_ids.py <csv path> 4169,260,262,410,5140

It reads the SMARD CSV (semicolon, German decimals, `-` as null), converts each
"Datum von" to epoch ms, downloads the weekly JSON chunks for each candidate filter ID,
and reports the CSV column whose values are closest hour by hour. A mean absolute
difference of 0.0000 is proof; anything above 0.5 is reported as no match.

## Saved samples

In `samples/`, all region DE, resolution hour, chunk 1789336800000 (week of Mon 14.09.2026):

| File | What it is |
|---|---|
| `smard_index_4067_hour.json` | the index: `{"timestamps": [...]}`, 613 weekly chunks, 28.12.2014 to 20.09.2026 |
| `smard_4067_wind_onshore_hour.json` | one generation chunk |
| `smard_4169_price_de_lu_hour.json` | one price chunk |
| `smard_410_netzlast_hour.json` | one load chunk |

Response shape for a data file:

```json
{"meta_data": {"version": 1, "created": 1789818769309},
 "series": [[1789336800000, 201.71], [1789340400000, 187.89], ...]}
```

- `series` is a list of `[timestamp_ms, value_or_null]`, 168 entries for a full hourly week.
- `meta_data.created` is when SMARD generated the file - useful as a source watermark.
- The index only lists chunks that exist, so it is the right way to plan a backfill.
- History goes back to the end of 2014: far more than the 90 days v1 needs.

## Publication lag: the one that changes the design

Measured at 15:52 Berlin on 22.09.2026 in the current chunk:

| Series | Newest value |
|---|---|
| Wind onshore (4067) | 22.09 14:00 - about 1.5 h behind now |
| Solar (4068) | 22.09 14:00 |
| Netzlast (410) | 22.09 14:00 |
| **Price DE/LU (4169)** | **23.09 23:00 - 33 hours into the future** |

The day-ahead auction publishes tomorrow's prices around midday, so the price series runs
*ahead* of real time while generation and load run *behind* it. Consequences for the pipeline:

- **Freshness means two different things.** For generation and load, freshness = how far behind
  now the newest value is (target: under 2 h). For price, the check is the opposite: tomorrow's
  prices should be present after ~13:00 Berlin, and their absence is the alarm.
- **The join must be inner, on realised hours only.** Joining price to generation blindly would
  produce rows with a price and no generation for every future hour, and any average computed
  over them would be wrong. Gold only contains hours where both sides are non-null.
- **The dashboard can honestly show a "next 24 hours" price strip** even in v1, clearly separated
  from the analysis, because that data genuinely exists. Not a forecast - published auction
  results. (Optional; not in the v1 scope list.)
