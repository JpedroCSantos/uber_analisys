WITH trip_sequences AS (
    SELECT
        vendor_id,
        pickup_at,
        dropoff_at,
        LAG(dropoff_at, 1) OVER (PARTITION BY vendor_id ORDER BY pickup_at) AS previous_dropoff_at
    FROM
        silver.fact_trips
    WHERE
        dropoff_at IS NOT NULL AND pickup_at IS NOT NULL
),
	
idle_times AS (
    SELECT
        vendor_id,
        (pickup_at - previous_dropoff_at) AS idle_time_interval
    FROM
        trip_sequences
    WHERE
        previous_dropoff_at IS NOT NULL AND pickup_at > previous_dropoff_at
)

SELECT
    v.name AS vendor_name,
    ROUND(
        AVG(EXTRACT(EPOCH FROM idle_time_interval) / 60),
        2
    ) AS average_idle_time_minutes
FROM
    idle_times i
JOIN
    silver.dim_vendor v ON i.vendor_id = v.vendor_id
GROUP BY
    v.name
ORDER BY
    average_idle_time_minutes DESC;