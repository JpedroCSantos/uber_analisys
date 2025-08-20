
--||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
-- SOLUÇÃO PROPOSTA
--||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

WITH total_days_in_period AS (
    SELECT
        COUNT(DISTINCT DATE_TRUNC('day', pickup_at)) AS distinct_days
    FROM
        silver.fact_trips_2025_01
)
SELECT
    ft.hour_of_day,
    CASE 
        WHEN EXTRACT(ISODOW FROM ft.pickup_at) IN (6, 7) THEN 'Fim de Semana'
        ELSE 'Dia de Semana'
    END AS day_type,
    COUNT(ft.trip_id) AS total_trips,
    ROUND(
        CAST(COUNT(ft.trip_id) AS NUMERIC) / (SELECT distinct_days FROM total_days_in_period), 
        2
    ) AS avg_trips_per_hour
FROM
    silver.fact_trips_2025_01 AS ft
CROSS JOIN
    total_days_in_period

GROUP BY
    ft.hour_of_day,
    day_type,
    total_days_in_period.distinct_days
ORDER BY
    day_type,
    ft.hour_of_day;

