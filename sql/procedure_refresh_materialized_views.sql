CREATE OR REPLACE PROCEDURE gold.refresh_materializes_views(
)LANGUAGE plpgsql
AS $$
BEGIN
	REFRESH MATERIALIZED VIEW gold.agg_trips_by_hour;
	REFRESH MATERIALIZED VIEW gold.vendor_summary;
	REFRESH MATERIALIZED VIEW gold.zone_payment_summary;
END;
$$;