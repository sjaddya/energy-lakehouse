# DWD Open Data notes (step a3)

Source: Deutscher Wetterdienst (DWD), Climate Data Center, open data server.

Step a3 deliverable: which DWD data this project uses, how it behaves, what it
cannot do, and how the one ambiguous thing about it was proved.

---

## 1. Source and licence

- Server: `https://opendata.dwd.de/` - no registration, no API key, no cookies.
- Everything used here lives under
  `https://opendata.dwd.de/climate_environment/CDC/observations_germany/climate/hourly/`.
- The server's own `README.txt` names the terms of use at
  `https://www.dwd.de/EN/service/legal_notice/legal_notice_node.html`, and the CDC
  terms are at `https://opendata.dwd.de/climate_environment/CDC/Terms_of_use.pdf`.
- DWD logs the requesting IP for up to 7 days; data is not shared with third parties.

**Licence, read 06.11.2026**

- `Terms_of_use.pdf` (status Mai 2024): *"Terms of use for data on the CDC-OpenData area.
  The **Creative Commons BY 4.0 - Licence "CC BY 4.0"** apply."*
- The attribution rules are set by §7 DWD-Gesetz and published at
  `https://www.dwd.de/DE/service/rechtliche_hinweise/vorlagen_quellenangabe.html`:
  - unchanged data, in text form: *"Quelle: Deutscher Wetterdienst"*
  - changed data, an example DWD gives itself: *"Datenbasis: Deutscher Wetterdienst,
    **Einzelwerte gemittelt**"*
- This project averages individual station values, so the second form is the correct one.

**Credit line used in the README and the dashboard footer**

> Datenbasis: Deutscher Wetterdienst, Einzelwerte gemittelt (CC BY 4.0) ·
> Data: Bundesnetzagentur | SMARD.de (CC BY 4.0)

---

## 2. URL and file-name patterns

```
station list:  {base}/{param}/recent/{PARAM}_Stundenwerte_Beschreibung_Stationen.txt
recent data:   {base}/{param}/recent/stundenwerte_{PARAM}_{id5}_akt.zip
historical:    {base}/{param}/historical/stundenwerte_{PARAM}_{id5}_{from}_{to}_hist.zip
radiation:     {base}/solar/stundenwerte_ST_{id5}_row.zip
column docs:   {base}/{param}/DESCRIPTION_obsgermany_climate_hourly_{param}_en.pdf
```

| Part | Meaning |
|---|---|
| `{param}` | folder name: `wind`, `sun`, `solar` |
| `{PARAM}` | file-name code: `FF` wind, `SD` sunshine, `ST` radiation |
| `{id5}` | station id padded to five digits: `4393` becomes `04393` |
| `_akt` | the rolling recent window, about 550 days, rewritten daily |
| `_hist` | the closed historical series |
| `_row` | radiation only: the whole series in one file, no recent/historical split |

- There is **no API**: one whole ZIP per station per parameter, no pagination, no
  query parameters, no incremental endpoint.
- `index_*.json` has no equivalent here. The station list is the only catalogue.

---

## 3. Parameters chosen, and what was rejected

| Folder | Parameter | Has `recent/`? | Stations | Data ended (checked 06.11.2026) | Decision |
|---|---|---|---|---|---|
| `wind/` | `F` hourly mean wind speed (m/s), `D` direction (degrees) | yes | 530 listed, 279 reporting | 04.11.2026 23:00 | **v1 input** |
| `sun/` | `SD_SO` sunshine duration per hour (minutes) | yes | 203 | 04.11.2026 23:00 | **v1 input** - the solar explanation |
| `solar/` | `FG_LBERG` global radiation (J/cm2), `FD_LBERG` diffuse | **no** | 41 | **30.09.2026** | **v2**, not v1 |

**Why radiation is not in v1**

- It ends about five weeks in the past, so it cannot sit behind a dashboard that
  claims two-hour freshness for the power data.
- Only 41 stations publish it, against 203 for sunshine duration.
- Each file is the entire series: 2 to 64 MB per station, 315 MB for the eight.

**What is lost by using minutes instead of W/m2**

- Minutes measure **how long** the sun shone, not **how strongly**. A hazy hour and a
  clear hour can both record 60 minutes.
- Sun angle is invisible. Sixty minutes in December and sixty in June deliver very
  different energy, so winter hours look sunnier than they produce.
- No direct/diffuse split, so a bright overcast hour cannot be told from a clear one.
- Net effect: the dashboard can say *"this was a sunny hour"*, not *"this much energy
  reached a panel"*. v1 only needs the first; a yield estimate in v2 needs radiation.

---

## 4. The station set

Eight stations, chosen so the weather side is geographically honest: wind capacity is
concentrated on the coast and in the north-east, solar capacity in the south.

| id | Station | Bundesland | Role | Lat | Lon | Wind rows | Sun rows |
|---|---|---|---|---|---|---|---|
| 04393 | Sankt Peter-Ording | Schleswig-Holstein | North Sea coast, offshore proxy | 54.33 | 8.60 | 13 196 | 10 349 |
| 03631 | Norderney | Niedersachsen | North Sea island | 53.71 | 7.15 | 13 200 | 10 474 |
| 00183 | Arkona | Mecklenburg-Vorpommern | Baltic coast, offshore proxy | 54.68 | 13.43 | 13 200 | 10 473 |
| 03987 | Potsdam | Brandenburg | onshore east | 52.38 | 13.06 | 13 200 | 10 471 |
| 00662 | Braunschweig | Niedersachsen | onshore centre | 52.29 | 10.45 | 13 199 | 10 475 |
| 01303 | Essen-Bredeney | Nordrhein-Westfalen | onshore west | 51.40 | 6.97 | 13 097 | 10 449 |
| 05404 | Weihenstephan-Durnast | Bayern | south, solar side | 48.40 | 11.69 | 13 116 | 10 416 |
| 04928 | Stuttgart (Schnarrenberg) | Baden-Wurttemberg | south-west, solar side | 48.83 | 9.20 | 13 193 | 10 426 |

- Window covered by all eight: **04.05.2025 to 04.11.2026 23:00 UTC** (the rolling
  `_akt` window, about 550 days = 13 200 hours).
- All eight report **both** wind and sunshine, so one station set serves both parameters.
- The wind row counts double as a gap rate: Essen-Bredeney is the worst at **103
  missing hours (0.8%)**, Sankt Peter-Ording next at 4. The rest are near-complete.
- Hourly values are averaged across **the stations that actually reported that hour**,
  never across all eight regardless - otherwise a missing station reports a calmer
  Germany than there was.

**Two stations kept deliberately as counter-examples, not as inputs**

| id | Station | Why it is kept |
|---|---|---|
| 00011 | Donaueschingen | wind runs to 2026 but its sunshine series ended in **2004** - proof that a station having one parameter does not mean it has the others |
| 00044 | Grossenkneten | listed inside `sun/recent/` but its data stops **02.03.2026** - proof that the folder does not mean the station is alive |

**The limitation: eight points standing in for a country**

- Eight ground measurements represent the weather over tens of thousands of turbines
  and millions of PV systems.
- Weather stations sit where a weather service needs them, **not where the capacity
  is**, and no land station measures the weather at an offshore wind farm.
- A plain average gives Arkona and Stuttgart equal weight although their regions carry
  very different installed capacity.
- The size of the gap is measured, not guessed: r = 0.80 for wind and 0.85 for
  sunshine, so the eight stations explain roughly **64 to 72 per cent** of the
  variation in national output. The rest is capacity distribution, outages,
  curtailment and offshore conditions.
- With more time: weight stations by installed capacity per Bundesland from the
  Marktstammdatenregister, or add two or three stations per region.
- Plain averaging stays in v1 because it hides nothing: no weights to justify, the
  result is reproducible from the station list, and the limitation is published on the
  dashboard rather than buried.

---

## 5. Column reference

| File | Header |
|---|---|
| wind | `STATIONS_ID;MESS_DATUM;QN_3;F;D;eor` |
| sun | `STATIONS_ID;MESS_DATUM;QN_7;SD_SO;eor` |
| radiation | `STATIONS_ID;MESS_DATUM;QN_592;ATMO_LBERG;FD_LBERG;FG_LBERG;SD_LBERG;ZENIT;MESS_DATUM_WOZ;eor` |

| Column | Meaning | Unit |
|---|---|---|
| `F` | hourly mean wind speed | m/s |
| `D` | wind direction | degrees |
| `SD_SO` | sunshine duration within the hour | minutes, 0-60 |
| `FG_LBERG` | hourly sum of global radiation | J/cm2 |
| `FD_LBERG` | hourly sum of diffuse radiation | J/cm2 |
| `SD_LBERG` | sunshine duration (radiation network) | minutes |
| `ATMO_LBERG` | long-wave downward radiation | J/cm2 |
| `ZENIT` | solar zenith angle | degrees |
| `MESS_DATUM_WOZ` | the same instant in true local solar time (wahre Ortszeit) | - |

| Convention | Detail |
|---|---|
| Timestamp | `MESS_DATUM` = `YYYYMMDDHH`, **UTC** for current data; radiation files carry odd minutes (`2026093023:15`) |
| Missing | `-999`. Never arithmetic, never zero |
| `eor` | literal end-of-row marker on every line; drop the column |
| `QN_*` | quality level. Recent rows carry a low value (provisional), older rows `10` (checked and corrected), so **old values change** |
| Encoding | latin-1, semicolon separated, fields padded with spaces |
| Unit conversion | W/m2 = J/cm2 x 10000 / 3600 = J/cm2 x 2.778 |

**What the metadata files inside each ZIP are for**

| File | Why it matters |
|---|---|
| `produkt_*.txt` | the data |
| `Metadaten_Parameter_*.txt` | unit, and `Zusatz-Info` gives the **time zone per period** (`Stundenwerte in MEZ` until 2002, `in UTC` after) |
| `Metadaten_Fehldaten_*.txt` | every missing period with exact timestamps and counts |
| `Metadaten_Geographie_*.txt` | coordinate and altitude changes - a station that moved is a break in the series |
| `Metadaten_Geraete_*.txt` | instrument changes - a step in the data with no weather behind it |

`Von_Datum` / `Bis_Datum` in those metadata files are the validity period of a
*metadata record*, at day precision ("this method applied from here to here"), not the
boundaries of an observation. Arkona's wind file holds five such records, the current
one running `20030901` to `20261104`.

---

## 6. Traps found, and what each means for the pipeline

| Trap | Proof | Pipeline consequence |
|---|---|---|
| A station inside `recent/` can be dead | `SD_00044` ends 02.03.2026 | select stations from the station list's `bis_datum`, never from the folder listing |
| The station lists have different freshness | wind list current to 04.11.2026, radiation list to 30.09.2026 | check each list separately; do not infer one from the other |
| A station can have one parameter and not another | `FF_00011` wind to 2026, sunshine ended 2004 | intersect the wind and sun station sets |
| A column can be empty at one station and present at another | `ATMO_LBERG` is `-999` at 04393, 112.0 at 00183 | column availability is per station, not per parameter |
| The sunshine files changed shape on **01.08.2026** | Arkona: every month from 05.2025 to 07.2026 has exactly 18 hours a day (03-20 UTC); from 08.2026 all 24. That is the whole 13 200 vs 10 473 row difference | a 90-day window today is complete; **a backfill before 01.08.2026 has 18 rows a day**. There an absent sunshine hour means **zero sun**, while an absent wind hour means **unknown** |
| Radiation files are the whole series | Arkona: 4.2 MB zipped, 34 MB and 388 584 rows back to 1981 | cannot be handled like the 70 KB wind files |
| No API, whole-file downloads, rewritten daily including corrected history | `QN` flags differ along one file | ingestion is "download the file, MERGE on (station, timestamp)"; the 48-hour re-fetch window that suits SMARD is too short here |
| Station lists are **fixed-width latin-1**, not CSV | station names contain spaces | slice by character position; splitting on whitespace corrupts the name and shifts every later field |

**The one that would have shipped silently: the hour label**

- Every other trap announces itself - a 404, a `-999`, a missing file, a row count
  that looks wrong.
- A one-hour shift raises nothing. The pipeline runs green, the chart looks
  plausible, and every quartile average is computed from the wrong weather.
- **Test for a17:** recompute the three correlations (lag -1, 0, +1) on a rolling
  90-day window each month, after the shift has been applied. **Lag 0 must be the
  strongest.** If the peak moves, DWD changed its convention and the run fails.
- Runner-up: the dead station in `recent/`. It would have silently dropped the set
  from eight stations to seven. **Test:** every configured station must report at
  least 90 per cent of expected hours in the window, or the run fails.

---

## 7. How the hour convention was proved

**The problem.** SMARD labels an hourly value by the **start** of the interval (its CSV
has `Datum von` and `Datum bis`). DWD gives one timestamp and no interval. If the two
conventions differ, every weather value joins one hour away from the generation it
explains - silently, with nothing failing.

**The method.** Build both series on a UTC hour key, shift the DWD side by -1, 0 and
+1 hours, and compute Pearson r each time over the hours present in both. The shift
with the highest r is the shift at which both labels mean the same instant. Pairs
chosen for physical causality: sunshine against solar generation, wind speed against
wind onshore generation.

**The result.** Window 07.08.2026 - 05.11.2026 UTC, 2 160 hours, weather averaged over
the eight stations. `lag -1` pairs DWD hour *t* with the SMARD interval starting at *t-1*.

| Pair | lag -1 | lag 0 | lag +1 | n |
|---|---|---|---|---|
| Sunshine `SD_SO` vs solar (4068) | **0.8462** | 0.8033 | 0.7063 | 2 160 |
| Wind speed `F` vs wind onshore (4067) | **0.8032** | 0.7954 | 0.7832 | 2 160 |

Repeated over 240 days, crossing the 01.08.2026 format change: sunshine
0.7962 / 0.7582 / 0.6677, wind 0.7662 / 0.7633 / 0.7549 - the same ordering.

**Conclusion.** Lag -1 wins in every variant, so **a DWD timestamp marks the end of the
hour it describes**. Silver subtracts one hour from `MESS_DATUM` before joining.

**How much to trust it.**

- Sunshine is the clean discriminator: 0.846 / 0.803 / 0.706 is a clear peak.
- Wind barely separates: 0.803 / 0.795 / 0.783. Turbine inertia and spatial smoothing
  blur a one-hour shift, so the wind pair agrees with the sunshine pair but could not
  have decided the question alone.
- Corroborating evidence from the metadata, found afterwards: `Metadaten_Parameter_ff_*`
  describes the aggregation window as `23:51-23:50 UTC`, i.e. windows that run from
  `:51` to `:50`. That points the same way, but it describes the daily gust window
  rather than the hourly label, so it supports the measurement instead of replacing it.
- Both r values are also a finding in their own right: eight stations explain roughly
  64 to 72 per cent of the variance in national output. That belongs on the dashboard.

Script: `tools/lag_check.py` (scratch tooling, stdlib only, not project code).
First-principles explanation of r and of the shift: `learning-log.md` 7.2.

**The interview answer**

> The documentation never states whether a DWD timestamp labels the start or the end
> of the hour, so I measured it: I correlated sunshine duration against solar
> generation at a shift of minus one, zero and plus one hour, and the correlation
> peaked clearly at minus one - 0.85 against 0.80 and 0.71.
>
> That told me DWD stamps the end of the hour while SMARD stamps the start, so silver
> shifts every DWD timestamp back by an hour. I ran the same test on wind speed, where
> it agreed but was too flat to be conclusive on its own, and the metadata's
> `23:51-23:50 UTC` aggregation window supports the same reading.

---

## 8. Saved samples

In `samples/`, downloaded 06.11.2026:

| File | What it is |
|---|---|
| `FF_Stundenwerte_Beschreibung_Stationen.txt` | wind station catalogue, 530 stations |
| `SD_Stundenwerte_Beschreibung_Stationen.txt` | sunshine station catalogue, 707 stations |
| `stundenwerte_FF_{id}_akt.zip` x8 | wind for the station set, 04.05.2025 - 04.11.2026 |
| `stundenwerte_SD_{id}_akt.zip` x8 | sunshine for the same eight, same window |
| `stundenwerte_ST_{id}_row.zip` x8 | radiation for the same eight - v2 material, ends 30.09.2026 |
| `stundenwerte_FF_00011_akt.zip` | counter-example: wind without a current sunshine series |
| `stundenwerte_SD_00044_akt.zip` | counter-example: a dead station inside `recent/` |
| `DESCRIPTION_*_en.pdf` x3 | official English column documentation, wind / sun / solar |
| `README.txt` | the open-data server README, which names the terms of use |

**Extraction layout**

- Each archive is unpacked into a folder beside it with the same name minus `.zip`;
  the ZIPs are kept.
- Wind and sunshine archives are unpacked in full (about 0.5 MB each).
- Radiation archives are unpacked **without** their `produkt_st_*.txt`: 315 MB in total
  and unused in v1. The file stays inside the ZIP, where `zipfile` can still read it.
- The pipeline never needs the extracted copies - `zipfile` reads a member straight out
  of the archive, which is how a12 should ingest it. The folders exist for reading the
  metadata by eye.

**Decision: the sample data is not committed to the repo.**

- `samples/` is excluded in `.gitignore` at a5. These notes live in the repo; the
  data files do not.
- Reason: size. The radiation archives alone are 315 MB unpacked, and git keeps every
  version of a binary forever.
- Reason: the data is already public and versioned at source. Committing a copy
  creates a second, stale truth.
- Reproducibility is kept by what **is** committed: the eight station ids, the exact
  URL patterns, the download date, and the row count per file recorded in section 8,
  so anyone can re-fetch and check the numbers against what is written here.

---

## 9. What this means for the build steps

| Step | What a3 fixed |
|---|---|
| a4 architecture | DWD is a file-download source, not an API source; it needs its own ingestion shape |
| a12 DWD ingestion | download one ZIP per station per parameter, read the member in place, MERGE on (station_id, timestamp_utc) |
| a13 silver | subtract one hour from `MESS_DATUM` into its own column (bronze keeps the published value); treat `-999` as null; treat an absent pre-01.08.2026 sunshine hour as zero **with a `sun_is_imputed` flag** but an absent wind hour as unknown; store UTC |
| a16 gold | average across reporting stations per hour, **only when at least six of eight reported**; inner join to the power data on realised hours |
| a17 tests | expected rows per station per day; sunshine between 0 and 60; wind speed not negative; the weather side no more than 48 hours stale; **the monthly lag check still peaks at 0** |
| a8/a12 ingestion | **check each station's `bis_datum` before fetching** - a dead station must fail loudly, not look like a gap |

**Four changes to that table, decided while writing it out**

- **An imputed zero must be visible.** Treating an absent pre-01.08.2026 sunshine hour
  as zero is right, but silver carries a `sun_is_imputed` flag next to it, so a chart
  can never present an assumption as a measurement.
- **Averaging needs a floor.** An hour is only usable if at least six of the eight
  stations reported; below that the hour is marked unreliable rather than averaged
  from two coastal stations.
- **The hour shift belongs in silver, never in bronze.** Bronze keeps `MESS_DATUM`
  exactly as published; silver writes the shifted UTC timestamp into its own column.
  If DWD ever changes convention, nothing has to be re-downloaded.
- **"Station is alive" is an ingestion check, not a dbt test.** By the time dbt runs,
  the missing station already looks like an ordinary gap. The loader compares the
  station list's `bis_datum` against today before it fetches anything.

---

Author: Soumyajeet Addya
Status: draft
Date: 06.11.2026
