WITH pu_location_amount_rank AS (
	SELECT
		pu_location_id,
		total_amount,
		-- RANK() OVER(PARTITION BY pu_location_id ORDER BY total_amount  DESC) AS total_rank
		-- DENSE_RANK() OVER(PARTITION BY pu_location_id ORDER BY total_amount  DESC) AS total_rank
		ROW_NUMBER() OVER(PARTITION BY pu_location_id ORDER BY total_amount  DESC) AS total_rank
	FROM 
		silver.fact_trips_2025_01
	WHERE total_amount > 0
)
SELECT
	dz.zone_name,
	rk.total_amount
	-- rk.total_rank
FROM pu_location_amount_rank AS rk
JOIN
	silver.dim_zone AS dz ON dz.zone_id = rk.pu_location_id
WHERE total_rank = 3
ORDER BY
	total_amount DESC
