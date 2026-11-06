# Project A — Problem statement (v1)

Author: Soumyajeet Addya <br>
Status: draft <br>
Date: 22.09.2026 <br>

## 1. The question

**Over the last 90 days, how much cheaper was Germany's wholesale electricity price in hours
with high wind and solar output than in hours with low output, and which weather conditions
produced those hours?**

Price is compared between the top and bottom quartile of renewable output, hour by hour, and
each hour is matched to the wind speed measured at that time.

## 2. Who asks it, and what they do with the answer

**A household on a dynamic electricity tariff** (Tibber, Rabot and similar, where the bill
follows the hourly wholesale price). The decision: which hours to charge the car or run the
heat pump. Instead of guessing, or looking at tomorrow's price curve with no idea why it is
shaped that way, they see how strongly a windy hour moves the price and how reliably that
holds.

**An energy analyst or a working student on an energy desk.** The decision: whether a price
spike or a very cheap hour is explained by the weather, or whether something else is going on
that is worth investigating. The dashboard gives them the expected price for that level of
renewable output, so the unusual hours stand out.

What exists today: SMARD publishes the price, the generation mix and the load, but each series
is charted on its own and nothing quantifies the relationship between them. Consumer apps show
tomorrow's prices without saying why they are high or low. Weather data sits in a separate
system again. Today someone has to join the three by eye.

## 3. The data that answers it

| Source | Series | Resolution | History needed | Why it is needed |
|---|---|---|---|---|
| SMARD (Bundesnetzagentur) | Day-ahead wholesale price, Germany/Luxembourg market area (EUR/MWh) | hourly | 90 days | Both sides of the headline number and the y-axis of the main chart |
| SMARD | Realised generation: wind onshore, wind offshore, solar | hourly | 90 days | The renewable output that splits the hours into quartiles; the x-axis |
| SMARD | Realised generation: conventional sources (grouped) | hourly | 90 days | Denominator for the renewable share; supporting view 1 |
| SMARD | Realised consumption / grid load (Netzlast) | hourly | 90 days | Supporting view 2, generation minus load |
| DWD Open Data | Hourly mean wind speed (m/s) and direction, eight stations: two North Sea coast, one Baltic, three onshore, two southern | hourly | 90 days | The weather side of the question: why output was high or low in that hour |
| DWD Open Data | Hourly sunshine duration (minutes), same eight stations | hourly | 90 days | The solar half of the weather explanation |

SMARD filter IDs, confirmed in step a2 by matching every hour against the published CSV:
**4169** day-ahead price Deutschland/Luxemburg, **4067** wind onshore, **1225** wind offshore,
**4068** solar, **410** Netzlast, plus the conventional group (1223, 4069, 4071, 4070, 1227)
and the remaining renewables (4066, 1226, 1228) for the renewable share. Data is served one
file per week, starting Monday 00:00 Berlin.

DWD stations, confirmed in step a3 and all reporting both wind and sunshine:
**04393** Sankt Peter-Ording, **03631** Norderney, **00183** Arkona, **03987** Potsdam,
**00662** Braunschweig, **01303** Essen-Bredeney, **05404** Weihenstephan-Dürnast,
**04928** Stuttgart. Values are averaged across the stations that reported each hour, and
this is published as a limitation: eight stations explain roughly 64 to 72 per cent of the
variation in national output, not all of it. Hourly global radiation was considered and
**deferred to v2**: it ends five weeks in the past and covers only 41 stations, so it cannot
sit behind a dashboard that claims two-hour freshness.

Measured in a3: a DWD timestamp marks the **end** of the hour it describes, while SMARD
labels an hour by its start, so one hour is subtracted from every DWD timestamp before the
join.

The three sources arrive at different times. The price series is published about 33 hours
**ahead** of real time, because the day-ahead auction settles the following day; generation
and load arrive about 1.5 hours **behind**; and the weather arrives about **1.5 days behind**.
Gold therefore contains only the hours where all the sides it needs are published, which
means the headline number covers roughly day −90 to day −2 rather than day −90 to now. The
dashboard states that window explicitly.

SMARD data is used under CC BY 4.0 and credited as "Bundesnetzagentur | SMARD.de" in the
README and in the dashboard footer.

## 4. The headline number and the main chart

**Headline number**

Over the last 90 days, hours in the top quartile of combined wind and solar output were
EUR __ /MWh cheaper than hours in the bottom quartile (EUR __ against EUR __).

**Main chart**

One point per hour for the last 90 days: combined wind and solar share of generation on the
x-axis, day-ahead price in EUR/MWh on the y-axis, with the two quartile averages marked.

**Supporting views (at most three)**

1. **Mix against price, last 7 days.** Hourly generation split into renewable and conventional,
   with the price drawn over it, so the shape of a single week is visible.
2. **Net exports, last 7 days.** Generation minus grid load per hour. This difference is
   dominated by cross-border trade, so it is labelled net exports and never as wasted energy.
   If SMARD also publishes a cross-border trade series (checked in a2) it is used to sanity-check
   this view; otherwise the view is labelled approximate.
3. **Cheap and negative hours.** The share of hours in the window with a price at or below zero,
   and the wind speed recorded in those hours.

**Precision note carried into the dashboard:** this is the wholesale day-ahead price in EUR/MWh,
not a retail tariff. The charging conclusion applies to households on a dynamic tariff; everyone
else pays a fixed rate and their bill does not move with these hours.

## 5. How pipeline health is judged

- **Freshness**, which means two different things here. Generation and load are published about
  an hour and a half after the fact, so the check is that gold is never more than 2 hours behind
  the newest published hour. The day-ahead price is published for the *following* day around
  midday, so for the price the check is the opposite: after 13:00 Berlin, tomorrow's hours must
  be present, and their absence is the alarm. The weather is a third case again: DWD rewrites
  one file per station per day, so the check is that the newest weather hour is no more than
  48 hours old. All three are shown on the dashboard.
- **Tests:** timestamp and price not null; one row per series per hour (unique timestamp);
  price within a plausible range of -500 to 4000 EUR/MWh, because negative prices are normal in
  Germany and must not be treated as errors; generation and load not negative; expected row count
  per day. A failing test fails the run rather than printing a warning.
- **Gaps:** missing hours are counted and shown on the dashboard, never silently dropped and
  never filled with invented values. Each run also re-fetches the last 48 hours, so values that
  the source corrects or publishes late are picked up.
- **When a source is down:** the loader retries with backoff; if it still fails the last good
  data stays in place, the run is marked failed and the dashboard shows that it is stale.

## 6. Out of scope for v1

- No price forecasting or any model; only what has already happened.
- No CO2 intensity.
- No per-region or per-bidding-zone breakdown; national figures only.
- No storage or curtailment analysis; the data sources do not answer how much energy could have
  been stored.
- No sub-hourly resolution, no alerts, no user accounts.

- No hourly solar radiation: it is published five weeks in arrears at only 41 stations, so
  sunshine duration is used instead. Radiation moves to v2.

Planned later: v2 adds CO2 intensity, the four grid regions and solar radiation; v3 adds a
price forecast model.
