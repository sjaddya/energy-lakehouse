-- A Berlin calendar day has 24 hours, except 23 on the March clock change and 25 on the
-- October one. Any other count means the UTC-to-Berlin conversion or the spine is wrong.
--
-- The first and last day of the loaded window are excluded, because they are genuinely
-- partial: the window starts and ends mid-day. Excluding them is the difference between
-- a test that asserts an invariant and a test that is red on arrival and gets ignored.

WITH edges AS (
    SELECT min(date_berlin) AS first_day,
           max(date_berlin) AS last_day
    FROM {{ ref('weather_germany_hourly') }}
),

per_day AS (
    SELECT w.date_berlin,
           count(DISTINCT w.hour_start_utc) AS hours
    FROM {{ ref('weather_germany_hourly') }} AS w
    CROSS JOIN edges AS e
    WHERE w.date_berlin > e.first_day
      AND w.date_berlin < e.last_day
    GROUP BY w.date_berlin
)

SELECT date_berlin, hours
FROM per_day
WHERE hours NOT IN (23, 24, 25)
