{{ config(materialized='view') }}

-- The windows the dashboard reads, resolved in one place.
--
-- hourly_market holds every hour and no date filter on purpose: a window is a
-- property of a claim, not of the data. That leaves every chart to work out
-- "the last 90 days" for itself, and the moment two of them disagree the screen
-- contradicts itself. The main chart would plot one 90 days while the headline
-- number printed beneath it describes another, with the two quartile averages
-- marked on hours that are not the hours being drawn. Nothing would error and
-- both numbers would be defensible on their own.
--
-- So both windows are resolved exactly once, here, with the same anchor
-- price_by_renewable_quartile uses: the newest Berlin day in the data, not
-- today. latest_day is published for the same reason the quartile model
-- publishes its bounds - an anchor that is not shown cannot be questioned.
--
-- A view rather than a table because it adds no facts. Every column of
-- hourly_market passes through untouched; the only new information is which
-- window each hour falls in, which is a filter, and materialising a filter
-- over a table in the same warehouse buys nothing and can go stale.

WITH bounds AS (
    SELECT max(date_berlin) AS latest_day
    FROM {{ ref('hourly_market') }}
)

SELECT m.*,
       b.latest_day,
       -- Inclusive of both ends, so headline_days of 90 spans 90 Berlin dates.
       -- A 25-hour changeover day therefore contributes 25 hours and a 23-hour
       -- one 23, which is correct: the window is a span of days, not of hours.
       (m.date_berlin >= date_sub(b.latest_day, {{ var('headline_days') - 1 }}))
           AS in_headline_window,
       (m.date_berlin >= date_sub(b.latest_day, {{ var('recent_days') - 1 }}))
           AS in_recent_window
FROM {{ ref('hourly_market') }} AS m
CROSS JOIN bounds AS b
