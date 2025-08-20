
--||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
-- SOLUÇÃO PROPOSTA
--||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
-- Usamos uma CTE para preparar os dados base antes da agregação final.
WITH base_data AS (
    SELECT
        trip_hour,
        day_type,
        total_trips,
        EXTRACT(DAY FROM (DATE_TRUNC('month', trip_hour) + INTERVAL '1 month' - INTERVAL '1 day')) AS days_in_month
    FROM 
        gold.agg_trips_by_hour
)

SELECT
    EXTRACT(MONTH FROM tby.trip_hour) AS trip_month,
    EXTRACT(YEAR FROM tby.trip_hour) AS trip_year,
    EXTRACT(HOUR FROM tby.trip_hour) AS hour_of_day,
    tby.day_type,
    MIN(tby.days_in_month) AS days_in_month,
    SUM(tby.total_trips) AS total_trips,
    ROUND(
        SUM(tby.total_trips)::NUMERIC / MIN(tby.days_in_month),
        2
    ) AS avg_daily_trips_for_hour
FROM 
    base_data AS tby
GROUP BY
    trip_month,
    trip_year,
    day_type,
    hour_of_day
ORDER BY
    trip_month,
    trip_year,
    day_type,
    hour_of_day;