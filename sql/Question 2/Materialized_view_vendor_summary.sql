CREATE MATERIALIZED VIEW IF NOT EXISTS gold.vendor_summary AS
SELECT
    v.name AS vendor_name,
    COUNT(ft.trip_id) AS total_trips,
    SUM(ft.passenger_count) AS total_passengers,
	ROUND(SUM(ft.trip_distance)::numeric, 2) AS total_distance_miles,
    ROUND(SUM(ft.total_amount)::numeric, 2) AS total_revenue,
    ROUND(AVG(ft.total_amount)::numeric, 2) AS avg_revenue_per_trip
FROM
    silver.fact_trips AS ft
JOIN
    silver.dim_vendor AS v ON ft.vendor_id = v.vendor_id
GROUP BY
    v.name
ORDER BY
    total_revenue DESC;

ALTER MATERIALIZED VIEW gold.vendor_summary OWNER TO admin_role;
CREATE UNIQUE INDEX IF NOT EXISTS idx_vendor_summary_name ON gold.vendor_summary (vendor_name);