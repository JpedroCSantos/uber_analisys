CREATE MATERIALIZED VIEW IF NOT EXISTS gold.agg_trips_by_hour AS
SELECT
    DATE_TRUNC('hour', ft.pickup_at) AS trip_hour,
    EXTRACT(ISODOW FROM ft.pickup_at) AS day_of_week,
    CASE 
        WHEN EXTRACT(ISODOW FROM ft.pickup_at) IN (6, 7) THEN 'Fim de Semana'
        ELSE 'Dia de Semana'
    END AS day_type,
    COUNT(*) AS total_trips,
    SUM(ft.total_amount) AS total_revenue,
    AVG(ft.trip_distance) AS avg_distance,
    AVG(ft.duration_minutes) AS avg_duration_minutes
FROM
    silver.fact_trips AS ft
GROUP BY
    1, 2, 3;

CREATE UNIQUE INDEX IF NOT EXISTS idx_agg_trips_by_hour ON gold.agg_trips_by_hour (trip_hour);

SELECT * FROM gold.agg_trips_by_hour