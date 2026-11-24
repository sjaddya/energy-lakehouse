-- dashboard_hours exists so that the main chart and the headline number describe the
-- same period. Its two window flags must each select exactly as many distinct Berlin
-- dates as their variable says - no more, because an off-by-one would put an extra day
-- on the chart that the headline never measured, and no fewer, because a short window
-- is how a stalled pipeline hides.
--
-- Day counts, not hour counts: a 25-hour changeover day contributes 25 hours and the
-- window is still 90 days. Asserting hours would make this test fail twice a year for
-- the one reason that is correct.

WITH counted AS (
    SELECT count(DISTINCT CASE WHEN in_headline_window THEN date_berlin END) AS headline_days,
           count(DISTINCT CASE WHEN in_recent_window   THEN date_berlin END) AS recent_days
    FROM {{ ref('dashboard_hours') }}
)

SELECT headline_days,
       recent_days
FROM counted
WHERE headline_days <> {{ var('headline_days') }}
   OR recent_days   <> {{ var('recent_days') }}
