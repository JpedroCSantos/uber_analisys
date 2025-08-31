WITH total_amount_per_day AS (
	SELECT
		DATE_TRUNC('day', pickup_at)::date AS trip_day,
		ROUND(SUM(total_amount),2) AS daily_total_revenue
	FROM
		silver.fact_trips_2025_01
	GROUP BY
		trip_day
	-- ORDER BY
	-- 	trip_day ASC
)
SELECT
	trip_day,
	daily_total_revenue,
	ROUND(AVG(daily_total_revenue) OVER(
		ORDER BY trip_day ASC 
		ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
	), 2) AS moving_avg_7_days
FROM 
	total_amount_per_day