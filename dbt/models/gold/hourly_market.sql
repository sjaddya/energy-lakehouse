-- One row per hour: the market, the mix and the weather side by side. This is
-- the table every chart reads, and the only place where the long silver power
-- table becomes one hour per row.
--
-- Three things happen here that are business logic rather than cleaning, which
-- is why this is gold and not silver:
--   * the thirteen series become named columns and two group totals
--   * generation minus load becomes net exports
--   * each hour carries the flags a chart needs to decide whether to trust it
--
-- The join to weather is LEFT, not INNER. Power covers 13441 hours and weather
-- 13200 of them, so an inner join would drop 241 hours of price and mix for
-- want of a wind speed the headline number never reads. has_weather names those
-- hours instead of hiding them.

WITH

-- How many series each group is supposed to have, counted from the seed rather
-- than typed here. sum() skips nulls, so an hour missing one generation series
-- yields a total that is clean, confident and too low. The only defence is to
-- count what arrived and compare it with what the lookup says exists.
expected AS (
    SELECT count(CASE WHEN series_group = 'renewable'    THEN 1 END) AS renewable_series,
           count(CASE WHEN series_group = 'conventional' THEN 1 END) AS conventional_series
    FROM {{ ref('series_lookup') }}
),

-- Silver holds one row per series per hour. max() over a group of one row is
-- that row's value: the standard pivot without a PIVOT clause, and sound here
-- only because (filter_id, hour_start_utc) is unique in silver.
hourly AS (
    SELECT hour_start_utc,
           max(hour_start_berlin)  AS hour_start_berlin,
           max(date_berlin)        AS date_berlin,
           max(hour_of_day_berlin) AS hour_of_day_berlin,

           max(CASE WHEN series_name = 'day_ahead_price_de_lu' THEN value END) AS day_ahead_price_eur_mwh,
           max(CASE WHEN series_name = 'grid_load'             THEN value END) AS grid_load_mwh,

           -- Named individually because the headline quartile is built on these
           -- three and nothing else. The rest only ever appear in the totals.
           max(CASE WHEN series_name = 'wind_onshore'  THEN value END) AS wind_onshore_mwh,
           max(CASE WHEN series_name = 'wind_offshore' THEN value END) AS wind_offshore_mwh,
           max(CASE WHEN series_name = 'solar_pv'      THEN value END) AS solar_pv_mwh,

           sum(CASE WHEN series_group = 'renewable'    THEN value END) AS renewable_mwh,
           sum(CASE WHEN series_group = 'conventional' THEN value END) AS conventional_mwh,

           count(CASE WHEN series_group = 'renewable'    THEN value END) AS renewable_series_realised,
           count(CASE WHEN series_group = 'conventional' THEN value END) AS conventional_series_realised,

           max(fetched_at) AS fetched_at
    FROM {{ ref('power_hourly') }}
    GROUP BY hour_start_utc
)

SELECT h.hour_start_utc,
       h.hour_start_berlin,
       h.date_berlin,
       h.hour_of_day_berlin,

       h.day_ahead_price_eur_mwh,
       h.grid_load_mwh,
       h.renewable_mwh,
       h.conventional_mwh,
       -- Null if either side is null. An hour whose mix is incomplete must not
       -- report a total, because a total is what a chart would believe.
       h.renewable_mwh + h.conventional_mwh AS generation_mwh,

       h.wind_onshore_mwh,
       h.wind_offshore_mwh,
       h.solar_pv_mwh,
       h.wind_onshore_mwh + h.wind_offshore_mwh + h.solar_pv_mwh AS wind_solar_mwh,

       -- try_divide returns null rather than failing when generation is zero,
       -- which happens in no real hour but would end a run if it ever did.
       try_divide(h.renewable_mwh, h.renewable_mwh + h.conventional_mwh) AS renewable_share,
       try_divide(h.wind_onshore_mwh + h.wind_offshore_mwh + h.solar_pv_mwh,
                  h.renewable_mwh + h.conventional_mwh)                 AS wind_solar_share,

       -- Dominated by cross-border trade, so it is net exports and never
       -- "wasted energy". The problem statement is explicit about that label.
       (h.renewable_mwh + h.conventional_mwh) - h.grid_load_mwh AS net_exports_mwh,

       h.renewable_series_realised,
       h.conventional_series_realised,
       (h.renewable_series_realised    = e.renewable_series
        AND h.conventional_series_realised = e.conventional_series) AS mix_is_complete,

       (h.day_ahead_price_eur_mwh IS NOT NULL) AS has_price,
       -- Negative prices are normal in Germany and are the point of view 3,
       -- not an error to be filtered out.
       (h.day_ahead_price_eur_mwh <= 0)        AS is_cheap_or_negative_price,

       (w.hour_start_utc IS NOT NULL)          AS has_weather,
       w.wind_speed_ms_avg,
       w.wind_direction_deg_avg,
       w.sunshine_minutes_avg,
       w.wind_is_reliable,
       w.sunshine_is_reliable,

       h.fetched_at
FROM hourly AS h
CROSS JOIN expected AS e
LEFT JOIN {{ ref('weather_germany_hourly') }} AS w
       ON w.hour_start_utc = h.hour_start_utc
