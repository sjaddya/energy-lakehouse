-- One row per hour for the whole country: an unweighted mean across the eight
-- stations. Each measure carries its own station count and reliability flag,
-- because one hour can have eight wind stations and five sunshine stations.

SELECT hour_start_utc,
       from_utc_timestamp(hour_start_utc, 'Europe/Berlin')       AS hour_start_berlin,
       date(from_utc_timestamp(hour_start_utc, 'Europe/Berlin')) AS date_berlin,
       hour(from_utc_timestamp(hour_start_utc, 'Europe/Berlin')) AS hour_of_day_berlin,

       avg(wind_speed_ms)                                        AS wind_speed_ms_avg,
       count(wind_speed_ms)                                      AS wind_stations,
       count(wind_speed_ms) >= {{ var('min_stations') }}         AS wind_is_reliable,

       -- Directions are angles, so they are averaged as unit vectors. The
       -- arithmetic mean of 350 and 10 is 180 - due south, when the wind is in
       -- fact from the north. mod(... + 360, 360) brings atan2 back into 0-360.
       mod(degrees(atan2(avg(sin(radians(wind_direction_deg))),
                         avg(cos(radians(wind_direction_deg))))) + 360, 360)
                                                                 AS wind_direction_deg_avg,

       avg(sunshine_minutes)                                     AS sunshine_minutes_avg,
       count(sunshine_minutes)                                   AS sunshine_stations,
       count(sunshine_minutes) >= {{ var('min_stations') }}      AS sunshine_is_reliable,
       sum(CASE WHEN sun_is_imputed THEN 1 ELSE 0 END)           AS sunshine_imputed_stations,

       max(fetched_at)                                           AS fetched_at
FROM {{ ref('weather_station_hourly') }}
GROUP BY hour_start_utc
