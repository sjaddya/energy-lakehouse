-- sun_is_imputed marks the night hours DWD never published, which silver fills with 0.0
-- because "the sun was not shining" is a known fact rather than a gap. The flag and the
-- value have to agree: an imputed row whose value is null, or is anything other than
-- zero, means the imputation and its audit trail have come apart.
--
-- This matters because sun_is_imputed is what lets a reader tell a measured zero from an
-- assumed one. A flag that can disagree with the value it describes is worse than no
-- flag, because it will still be trusted.

SELECT station_id,
       hour_start_utc,
       sunshine_minutes,
       sun_is_imputed
FROM {{ ref('weather_station_hourly') }}
WHERE sun_is_imputed
  AND (sunshine_minutes IS NULL OR sunshine_minutes <> 0)
