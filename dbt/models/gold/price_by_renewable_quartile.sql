-- The headline number of the project, as four rows. Hours in the window are
-- split into quartiles by combined wind and solar output, and each quartile
-- reports what the price did. Section 4 of the problem statement reads the top
-- and the bottom row; the two middle rows are what show whether the difference
-- is a trend or an artefact of picking two ends.
--
-- The window lives here and not in hourly_market, because 90 days is a property
-- of this claim rather than of the data. Every chart that reads hourly_market
-- keeps all of its hours.

WITH

-- The window is anchored on the newest day the table holds, not on today. If it
-- were anchored on current_date, a pipeline that stopped loading would quietly
-- shrink the window - the headline would be computed from a handful of hours and
-- would still look perfectly healthy. Anchoring on the data means the window is
-- always the full span asked for; a stale window is a19's alarm to raise, with
-- its own explicit check. The price of that choice is that the bounds have to be
-- published, which is why they are columns below.
bounds AS (
    SELECT max(date_berlin)                                           AS window_end_berlin,
           date_sub(max(date_berlin), {{ var('headline_days') - 1 }}) AS window_start_berlin
    FROM {{ ref('hourly_market') }}
),

windowed AS (
    SELECT m.hour_start_utc,
           m.wind_solar_mwh,
           m.day_ahead_price_eur_mwh,
           m.renewable_share,
           m.wind_speed_ms_avg,
           m.has_weather,
           m.is_cheap_or_negative_price,
           b.window_start_berlin,
           b.window_end_berlin
    FROM {{ ref('hourly_market') }} AS m
    CROSS JOIN bounds AS b
    WHERE m.date_berlin BETWEEN b.window_start_berlin AND b.window_end_berlin
      -- An hour with no published price cannot be compared on price, and an
      -- hour with a partial generation mix would be sorted on a wind and solar
      -- total that is missing a part. Both are excluded rather than imputed.
      AND m.has_price
      AND m.mix_is_complete
),

-- ntile splits by row count, so it needs a total order to be reproducible: two
-- hours with identical output would otherwise land in different quartiles from
-- one run to the next. hour_start_utc is the tiebreak because it is unique.
ranked AS (
    SELECT *,
           ntile(4) OVER (ORDER BY wind_solar_mwh, hour_start_utc) AS quartile
    FROM windowed
),

per_quartile AS (
    SELECT quartile,
           count(*)                                                AS hours,

           min(wind_solar_mwh)                                     AS wind_solar_mwh_min,
           avg(wind_solar_mwh)                                     AS wind_solar_mwh_avg,
           max(wind_solar_mwh)                                     AS wind_solar_mwh_max,

           avg(day_ahead_price_eur_mwh)                            AS day_ahead_price_eur_mwh_avg,
           avg(renewable_share)                                    AS renewable_share_avg,

           -- avg() skips nulls, so this mean is taken over the hours that have
           -- weather and not over the quartile. hours_with_weather is its
           -- denominator, published so the mean can be read honestly.
           avg(wind_speed_ms_avg)                                  AS wind_speed_ms_avg,
           count(wind_speed_ms_avg)                                AS hours_with_weather,

           sum(CASE WHEN is_cheap_or_negative_price THEN 1 ELSE 0 END) AS cheap_or_negative_hours,

           max(window_start_berlin)                                AS window_start_berlin,
           max(window_end_berlin)                                  AS window_end_berlin
    FROM ranked
    GROUP BY quartile
)

SELECT quartile,
       hours,
       wind_solar_mwh_min,
       wind_solar_mwh_avg,
       wind_solar_mwh_max,
       day_ahead_price_eur_mwh_avg,

       -- The headline difference, as a single cell. first_value over the
       -- quartile order is quartile 1's average, so the bottom row reads 0 and
       -- the top row reads the number section 4 asks for. Computing it here
       -- rather than in the dashboard means one definition of "cheaper".
       day_ahead_price_eur_mwh_avg
           - first_value(day_ahead_price_eur_mwh_avg) OVER (ORDER BY quartile)
                                                        AS price_eur_mwh_vs_bottom_quartile,

       renewable_share_avg,
       wind_speed_ms_avg,
       hours_with_weather,
       cheap_or_negative_hours,
       try_divide(cheap_or_negative_hours, hours)       AS cheap_or_negative_share,

       window_start_berlin,
       window_end_berlin,
       {{ var('headline_days') }}                       AS window_days,
       sum(hours) OVER ()                               AS hours_in_window
FROM per_quartile
ORDER BY quartile
