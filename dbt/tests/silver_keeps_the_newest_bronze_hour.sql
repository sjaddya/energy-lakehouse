-- DWD labels an observation with the hour it ENDS; silver shifts it back one hour to
-- match SMARD's hour start. The newest silver hour must therefore be exactly one hour
-- before the newest bronze hour.
--
-- An off-by-one in that shift is close to undetectable by eye: the table still has the
-- right number of rows, every hour still looks plausible, and the only symptom is that
-- weather and power are misaligned by an hour - which shows up as a slightly weaker
-- correlation, not as an error. a8 measured that shift rather than guessing it
-- (0.846 at one hour, against 0.803 at zero). This test is what stops the measurement
-- from having to be repeated.

SELECT b.last_bronze_hour,
       s.last_silver_hour
FROM (SELECT max(timestamp_utc) AS last_bronze_hour
      FROM {{ source('bronze', 'dwd_raw') }}) AS b
CROSS JOIN (SELECT max(hour_start_utc) AS last_silver_hour
            FROM {{ ref('weather_station_hourly') }}) AS s
WHERE s.last_silver_hour <> b.last_bronze_hour - INTERVAL 1 HOUR
