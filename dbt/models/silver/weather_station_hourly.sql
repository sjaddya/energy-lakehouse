-- One row per station and hour, on a spine that holds every hour in range for
-- every station. A station that published nothing for an hour gets a null row,
-- not no row: "we looked and there was nothing" is a different fact from
-- "we never looked", and only the spine can tell them apart.
--
-- DWD labels an observation with the hour it ENDS. SMARD labels the hour it
-- starts. The shift of one hour below is what makes the two joinable at all.

WITH shifted AS (
    SELECT station_id,
           timestamp_utc - INTERVAL 1 HOUR AS hour_start_utc,
           parameter,
           value,
           quality,
           fetched_at
    FROM {{ source('bronze', 'dwd_raw') }}
),

-- Bronze holds one row per parameter. Silver holds one row per station-hour, so
-- the three parameters become three columns. max() over a group of one is just
-- that value; it is the standard way to pivot without a PIVOT clause.
wide AS (
    SELECT station_id,
           hour_start_utc,
           max(CASE WHEN parameter = 'wind_speed_ms'      THEN value   END) AS wind_speed_ms,
           max(CASE WHEN parameter = 'wind_direction_deg' THEN value   END) AS wind_direction_deg,
           max(CASE WHEN parameter = 'sunshine_minutes'   THEN value   END) AS sunshine_minutes,
           max(CASE WHEN parameter = 'wind_speed_ms'      THEN quality END) AS wind_quality,
           max(CASE WHEN parameter = 'sunshine_minutes'   THEN quality END) AS sun_quality,
           max(fetched_at)                                                  AS fetched_at
    FROM shifted
    GROUP BY station_id, hour_start_utc
),

bounds AS (
    SELECT min(hour_start_utc) AS first_hour,
           max(hour_start_utc) AS last_hour
    FROM wide
),

spine AS (
    SELECT lk.station_id,
           lk.station_name,
           lk.state,
           explode(sequence(b.first_hour, b.last_hour, INTERVAL 1 HOUR)) AS hour_start_utc
    FROM {{ ref('station_lookup') }} AS lk
    CROSS JOIN bounds AS b
),

joined AS (
    SELECT sp.hour_start_utc,
           sp.station_id,
           sp.station_name,
           sp.state,
           hour(sp.hour_start_utc) IN ({{ var('night_hours_utc') | join(', ') }}) AS is_night_hour,
           w.wind_speed_ms,
           w.wind_direction_deg,
           w.sunshine_minutes AS sunshine_minutes_raw,
           w.wind_quality,
           w.sun_quality,
           w.fetched_at
    FROM spine AS sp
    LEFT JOIN wide AS w
           ON w.station_id = sp.station_id
          AND w.hour_start_utc = sp.hour_start_utc
)

SELECT hour_start_utc,
       from_utc_timestamp(hour_start_utc, 'Europe/Berlin')       AS hour_start_berlin,
       date(from_utc_timestamp(hour_start_utc, 'Europe/Berlin')) AS date_berlin,
       hour(from_utc_timestamp(hour_start_utc, 'Europe/Berlin')) AS hour_of_day_berlin,
       station_id,
       station_name,
       state,
       wind_speed_ms,
       wind_direction_deg,
       -- A night hour DWD never published is a known zero, not a gap. Anything
       -- else missing stays null, and sun_is_imputed says which is which.
       CASE WHEN sunshine_minutes_raw IS NOT NULL THEN sunshine_minutes_raw
            WHEN is_night_hour                    THEN 0.0
       END AS sunshine_minutes,
       (sunshine_minutes_raw IS NULL AND is_night_hour) AS sun_is_imputed,
       wind_quality,
       sun_quality,
       fetched_at
FROM joined
