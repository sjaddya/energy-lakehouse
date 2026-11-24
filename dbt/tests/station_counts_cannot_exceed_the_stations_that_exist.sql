-- wind_stations and sunshine_stations count how many stations contributed to an hourly
-- mean. The bound is not the literal 8: it is however many rows station_lookup has, read
-- from the seed. Writing 8 would pass today and be wrong the day a ninth station is
-- added - the same failure mode as the ingestion constant in a16.
--
-- A count above the bound means the spine let a station-hour in twice, which would
-- silently weight one station double in every average it touches.

SELECT g.hour_start_utc,
       g.wind_stations,
       g.sunshine_stations,
       lk.stations_that_exist
FROM {{ ref('weather_germany_hourly') }} AS g
CROSS JOIN (SELECT count(*) AS stations_that_exist
            FROM {{ ref('station_lookup') }}) AS lk
WHERE g.wind_stations     > lk.stations_that_exist
   OR g.sunshine_stations > lk.stations_that_exist
   OR g.wind_stations     < 0
   OR g.sunshine_stations < 0
