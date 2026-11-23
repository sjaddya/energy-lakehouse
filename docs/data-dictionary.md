# Data dictionary

Every table in the `energy` catalog, generated from `information_schema` by
`notebooks/metadata`. Do not edit by hand: re-run that notebook instead.

It carries no generation date on purpose, so re-running it produces an identical file
unless the schema itself changed, and a diff always means something real.

Nullability is not listed. Every column in this catalog is nullable at the storage level,
because a silver table is rebuilt with CREATE OR REPLACE on every run and a column
constraint would not survive the rebuild. Which columns are required is asserted by the
data tests in a17 instead, where the assertion runs after each rebuild rather than before it.

## `energy.bronze`

Raw source data as published, plus the run that fetched it. Nothing is cleaned, renamed or joined here. A bronze row answers one question: what did the source say, and when did we get it.

### `energy.bronze.dwd_raw`

Hourly wind and sunshine observations from eight DWD stations: one row per station, hour and parameter, read from the recent archives. Merged on (station_id, timestamp_utc, parameter). Datenbasis: Deutscher Wetterdienst, Einzelwerte gemittelt. Licensed CC BY 4.0.

| # | Column | Type | Meaning |
|---|---|---|---|
| 1 | `station_id` | `string` | Five-digit DWD station id, zero padded, for example 00183 for Arkona. |
| 2 | `timestamp_utc` | `timestamp` | The hour as DWD labels it, which is the hour END. Silver shifts it back one hour so it lines up with the SMARD hour start. |
| 3 | `parameter` | `string` | Which measurement this row holds: wind_speed_ms, wind_direction_deg or sunshine_minutes. |
| 4 | `value` | `double` | The observation. The DWD missing marker -999 is converted to null when the file is parsed. |
| 5 | `quality` | `int` | DWD quality level (QN) reported for the measurement. |
| 6 | `source_file` | `string` | Path of the DWD archive this row was read from. |
| 7 | `load_id` | `string` | UUID of the notebook run that wrote this row. |
| 8 | `fetched_at` | `timestamp` | UTC time the run started. Freshness is measured against max(fetched_at), never against now(): the two answer different questions. |

### `energy.bronze.smard_raw`

German electricity generation, consumption and day-ahead price: one row per series and hour, as published by SMARD. Merged on (filter_id, timestamp_utc), so re-running a load corrects values instead of duplicating them. Source: Bundesnetzagentur | SMARD.de, licensed CC BY 4.0.

| # | Column | Type | Meaning |
|---|---|---|---|
| 1 | `filter_id` | `int` | SMARD series id, for example 4068 for solar PV. Resolved to a name in silver. |
| 2 | `timestamp_utc` | `timestamp` | Start of the hour the value applies to, in UTC, exactly as SMARD publishes it. |
| 3 | `value` | `double` | The published value in the unit of its series. Null where SMARD has padded the current week ahead of publication, which is why count(*) and count(value) answer different questions. |
| 4 | `source_chunk` | `bigint` | Id of the weekly SMARD file this row came from. Used as the high-water mark so a load fetches only the weeks bronze does not already hold. |
| 5 | `load_id` | `string` | UUID of the notebook run that wrote this row. |
| 6 | `fetched_at` | `timestamp` | UTC time the run started. Freshness is measured against max(fetched_at), never against now(): the two answer different questions. |

## `energy.silver`

One clean, conformed row per hour. UTC hour starts with Berlin labels alongside, source codes resolved to names, and every table rebuilt in full from bronze on each run rather than merged incrementally.

### `energy.silver.power_hourly`

One row per series and hour. The SMARD filter_id is resolved to a series name, group and unit through a left join, and Berlin calendar labels sit alongside the UTC hour start. Full rebuild from bronze.smard_raw.

| # | Column | Type | Meaning |
|---|---|---|---|
| 1 | `hour_start_utc` | `timestamp` | Start of the hour the row describes, in UTC. The join key between power and weather. |
| 2 | `hour_start_berlin` | `timestamp` | The same instant written as Berlin wall-clock time. A label, not an instant: on the October clock change two different UTC hours carry the same Berlin label. |
| 3 | `date_berlin` | `date` | Berlin calendar date. Note that (date_berlin, hour_of_day_berlin) is NOT a unique key: local hour 2 occurs twice on the October clock-change date. |
| 4 | `hour_of_day_berlin` | `int` | Berlin hour of day, 0 to 23. See date_berlin for why it is not part of a key. |
| 5 | `filter_id` | `int` | SMARD series id, carried unchanged from bronze. |
| 6 | `series_name` | `string` | Human-readable series name, for example wind_onshore. Null would mean a filter_id the project does not know; the load check asserts it never is. |
| 7 | `series_group` | `string` | One of renewable, conventional, price or load. |
| 8 | `unit` | `string` | MWh for every series except the day-ahead price, which is EUR/MWh. |
| 9 | `value` | `double` | The published value, carried unchanged from bronze. Null where SMARD has not published yet. |
| 10 | `load_id` | `string` | UUID of the notebook run that wrote this row. |
| 11 | `fetched_at` | `timestamp` | UTC time the run started. Freshness is measured against max(fetched_at), never against now(): the two answer different questions. |

### `energy.silver.weather_germany_hourly`

One row per hour: an unweighted mean across the eight stations, with the number of contributing stations and a reliability flag for each measure. Wind direction uses a circular mean. Full rebuild from silver.weather_station_hourly.

| # | Column | Type | Meaning |
|---|---|---|---|
| 1 | `hour_start_utc` | `timestamp` | Start of the hour the row describes, in UTC. The join key between power and weather. |
| 2 | `hour_start_berlin` | `timestamp` | The same instant written as Berlin wall-clock time. A label, not an instant: on the October clock change two different UTC hours carry the same Berlin label. |
| 3 | `date_berlin` | `date` | Berlin calendar date. Note that (date_berlin, hour_of_day_berlin) is NOT a unique key: local hour 2 occurs twice on the October clock-change date. |
| 4 | `hour_of_day_berlin` | `int` | Berlin hour of day, 0 to 23. See date_berlin for why it is not part of a key. |
| 5 | `wind_speed_ms_avg` | `double` | Unweighted mean wind speed across the stations that reported this hour. |
| 6 | `wind_stations` | `bigint` | How many of the eight stations contributed a wind reading. |
| 7 | `wind_is_reliable` | `boolean` | True when at least six stations reported wind. Kept separate from sunshine_is_reliable because one hour can have eight wind stations and five sun stations. |
| 8 | `wind_direction_deg_avg` | `double` | Circular mean of the station directions, 0 to 360. The arithmetic mean of 350 and 10 would be 180, due south, when the wind is in fact from the north. |
| 9 | `sunshine_minutes_avg` | `double` | Unweighted mean sunshine minutes across the stations that reported this hour. |
| 10 | `sunshine_stations` | `bigint` | How many of the eight stations contributed a sunshine value. |
| 11 | `sunshine_is_reliable` | `boolean` | True when at least six stations reported sunshine. |
| 12 | `sunshine_imputed_stations` | `bigint` | How many of the contributing stations had sunshine imputed to zero for this hour, so an average built mostly from imputed zeros can be told apart from a measured one. |
| 13 | `fetched_at` | `timestamp` | The most recent fetch that touched any station-hour inside this hour. |

### `energy.silver.weather_station_hourly`

One row per station and hour on a complete hourly spine, so a missing observation appears as a null row rather than as no row at all. DWD labels the hour end, so timestamps are shifted back one hour to match the SMARD hour start. Full rebuild from bronze.dwd_raw.

| # | Column | Type | Meaning |
|---|---|---|---|
| 1 | `hour_start_utc` | `timestamp` | Start of the hour, UTC, already shifted back one hour from the DWD hour-end label so it lines up with power_hourly. |
| 2 | `hour_start_berlin` | `timestamp` | The same instant written as Berlin wall-clock time. A label, not an instant: on the October clock change two different UTC hours carry the same Berlin label. |
| 3 | `date_berlin` | `date` | Berlin calendar date. Note that (date_berlin, hour_of_day_berlin) is NOT a unique key: local hour 2 occurs twice on the October clock-change date. |
| 4 | `hour_of_day_berlin` | `int` | Berlin hour of day, 0 to 23. See date_berlin for why it is not part of a key. |
| 5 | `station_id` | `string` | Five-digit DWD station id, zero padded. |
| 6 | `station_name` | `string` | Station name exactly as the DWD catalogue spells it. |
| 7 | `state` | `string` | German federal state the station sits in. |
| 8 | `wind_speed_ms` | `double` | Mean wind speed in metres per second. Null where the station published nothing for this hour. |
| 9 | `wind_direction_deg` | `double` | Wind direction in degrees, 0 to 360, meaning the direction the wind comes FROM. Must be averaged circularly, never arithmetically. |
| 10 | `sunshine_minutes` | `double` | Minutes of sunshine in the hour, 0 to 60. Imputed to 0.0 for the night hours DWD never published; see sun_is_imputed. |
| 11 | `sun_is_imputed` | `boolean` | True where sunshine_minutes was set to 0.0 because the hour is one of the six night hours (UTC 0, 1, 20, 21, 22, 23) that DWD did not publish before August 2026. Every other missing value is left null. |
| 12 | `wind_quality` | `int` | DWD quality level for the wind measurement, carried from bronze. |
| 13 | `sun_quality` | `int` | DWD quality level for the sunshine measurement, carried from bronze. |
| 14 | `fetched_at` | `timestamp` | The most recent fetch that touched this station-hour. Null means the hour never arrived in any file. load_id is deliberately absent here: a station-hour is built from two archives that can be loaded by different runs, so no single run id describes the whole row. |

## `energy.gold`

Business-level tables built to answer a question rather than to mirror a source. Deliberately empty until a16.

_No tables yet._
