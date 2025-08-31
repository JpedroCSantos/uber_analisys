CREATE MATERIALIZED VIEW IF NOT EXISTS gold.zone_payment_summary AS (
	SELECT
		ft.pu_location_id,
		dz.borough,
		dz.zone_name,
		dpt.description AS payment_name,
		COUNT(ft.trip_id) AS total_trips,
		SUM(ft.duration_minutes) AS total_duration_minutes,
		AVG(ft.duration_minutes) AS avg_duration_minutes,
		SUM(ft.passenger_count) as total_passenger,
		AVG(ft.passenger_count) as avg_passenger,
		SUM(ft.trip_distance) as total_distance,
		AVG(ft.trip_distance) as avg_distance,
		SUM(ft.tip_amount) AS total_tip_amount,
		AVG(ft.tip_amount) AS avg_tip_amount,
		SUM(ft.total_amount) AS total_amount,
		AVG(ft.total_amount) AS avg_amount
	FROM 
		silver.fact_trips AS ft
	JOIN 
		silver.dim_payment_type AS dpt ON ft.payment_type = dpt.payment_type_id
	JOIN 
		silver.dim_zone AS dz ON dz.zone_id = ft.pu_location_id
	GROUP BY
		ft.pu_location_id,
		dz.borough,
		dz.zone_name,
		ft.payment_type,
		dpt.description
)

ALTER MATERIALIZED VIEW gold.zone_payment_summary OWNER TO admin_role;