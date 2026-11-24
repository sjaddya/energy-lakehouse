-- The most important test in this project.
--
-- a16 began by discovering that eight of the thirteen series the project claims to
-- cover had no data at all, for months, because the ingestion constant was a
-- hand-written subset of the named series. Nothing failed. Every query ran. The
-- charts would have been clean, confident and about five series.
--
-- The query that would have caught it was written as a notebook cell - realised_rows
-- per series - and printed a number nobody compared against anything. This is that
-- cell with the comparison written down: a series the project names in its lookup
-- and cannot show a single realised value for is a failure, not a row of output.

SELECT s.filter_id,
       s.series_name
FROM {{ ref('series_lookup') }} AS s
LEFT JOIN {{ ref('power_hourly') }} AS p
       ON p.filter_id = s.filter_id
      AND p.value IS NOT NULL
GROUP BY s.filter_id, s.series_name
HAVING count(p.value) = 0
