-- One clean hour per SMARD series. The only change from bronze is the join that
-- resolves filter_id to a readable name, and the Berlin calendar labels.
--
-- The join is LEFT on purpose: an unknown filter_id must appear as a row with a
-- null series_name, not vanish. a17 adds the test that asserts it never happens.

SELECT
    b.timestamp_utc                                            AS hour_start_utc,
    from_utc_timestamp(b.timestamp_utc, 'Europe/Berlin')       AS hour_start_berlin,
    date(from_utc_timestamp(b.timestamp_utc, 'Europe/Berlin')) AS date_berlin,
    hour(from_utc_timestamp(b.timestamp_utc, 'Europe/Berlin')) AS hour_of_day_berlin,
    b.filter_id,
    s.series_name,
    s.series_group,
    s.unit,
    b.value,
    b.load_id,
    b.fetched_at
FROM {{ source('bronze', 'smard_raw') }} AS b
LEFT JOIN {{ ref('series_lookup') }} AS s
       ON s.filter_id = b.filter_id
