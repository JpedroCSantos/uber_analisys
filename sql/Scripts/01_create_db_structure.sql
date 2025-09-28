-- =============================================================================
-- SCRIPT ÚNICO DE CRIAÇÃO DE ESTRUTURA (ROLES, SCHEMAS, TABELAS BASE E LOG)
-- Agrupa: create_schemas_and_tables.sql + table_file_log.sql
-- Ajuste: concede admin_role ao usuário atual logo após a criação
-- =============================================================================

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'admin_role'
    ) THEN
        CREATE ROLE admin_role WITH
          NOLOGIN
          NOSUPERUSER
          NOCREATEDB
          NOCREATEROLE
          INHERIT
          NOREPLICATION
          CONNECTION LIMIT -1;
    END IF;
END $$;

GRANT admin_role TO CURRENT_USER;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'etl_role'
    ) THEN
        CREATE ROLE etl_role WITH NOLOGIN INHERIT;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'analyst_role'
    ) THEN
        CREATE ROLE analyst_role WITH NOLOGIN INHERIT;
    END IF;
    IF NOT EXISTS (
        SELECT 1 FROM pg_roles WHERE rolname = 'api_role'
    ) THEN
        CREATE ROLE api_role WITH NOLOGIN INHERIT;
    END IF;
END $$;

CREATE SCHEMA IF NOT EXISTS bronze AUTHORIZATION admin_role;
CREATE SCHEMA IF NOT EXISTS silver AUTHORIZATION admin_role;
CREATE SCHEMA IF NOT EXISTS gold AUTHORIZATION admin_role;

CREATE TABLE IF NOT EXISTS bronze.raw_trips_landing (
    vendor_id               TEXT,
    tpep_pickup_datetime    TEXT,
    tpep_dropoff_datetime   TEXT,
    passenger_count         TEXT,
    trip_distance           TEXT,
    ratecode_id             TEXT,
    store_and_fwd_flag      TEXT,
    pu_location_id          TEXT,
    do_location_id          TEXT,
    payment_type            TEXT,
    fare_amount             TEXT,
    extra                   TEXT,
    mta_tax                 TEXT,
    tip_amount              TEXT,
    tolls_amount            TEXT,
    improvement_surcharge   TEXT,
    total_amount            TEXT,
    congestion_surcharge    TEXT,
    airport_fee             TEXT,
    cbd_congestion_fee      TEXT
);
ALTER TABLE bronze.raw_trips_landing OWNER TO admin_role;

CREATE TABLE IF NOT EXISTS silver.dim_vendor (
    vendor_id           SMALLINT PRIMARY KEY,
    name                TEXT NOT NULL
);
ALTER TABLE silver.dim_vendor OWNER TO admin_role;

CREATE TABLE IF NOT EXISTS silver.dim_rate_code (
    rate_code_id        SMALLINT PRIMARY KEY,
    description         TEXT NOT NULL
);
ALTER TABLE silver.dim_rate_code OWNER TO admin_role;

CREATE TABLE IF NOT EXISTS silver.dim_payment_type (
    payment_type_id     SMALLINT PRIMARY KEY,
    description         TEXT NOT NULL
);
ALTER TABLE silver.dim_payment_type OWNER TO admin_role;

CREATE TABLE IF NOT EXISTS silver.dim_zone (
  zone_id       SMALLINT PRIMARY KEY,
  borough       TEXT NOT NULL,
  zone_name     TEXT NOT NULL
);
ALTER TABLE silver.dim_zone OWNER TO admin_role;

CREATE TABLE IF NOT EXISTS silver.fact_trips (
    trip_id                 BIGINT GENERATED ALWAYS AS IDENTITY,
    vendor_id               SMALLINT REFERENCES silver.dim_vendor(vendor_id),
    passenger_count         SMALLINT CHECK (passenger_count >= 0 AND passenger_count <= 6),
    trip_distance           NUMERIC(7,3) CHECK (trip_distance >= 0),
    ratecode_id            	SMALLINT REFERENCES silver.dim_rate_code(rate_code_id),
    store_and_fwd_flag      BOOLEAN,
    payment_type	        SMALLINT REFERENCES silver.dim_payment_type(payment_type_id),
    fare_amount             NUMERIC(10,2),
    extra                   NUMERIC(10,2),
    mta_tax                 NUMERIC(10,2),
    tip_amount              NUMERIC(10,2),
    tolls_amount            NUMERIC(10,2),
    improvement_surcharge   NUMERIC(10,2),
    congestion_surcharge    NUMERIC(10,2),
    total_amount            NUMERIC(10,2),
    airport_fee             NUMERIC(10,2),
    cbd_congestion_fee      NUMERIC(10,2),
    pickup_at               TIMESTAMPTZ NOT NULL,
    dropoff_at              TIMESTAMPTZ NOT NULL,
    duration_minutes        NUMERIC(6,2) CHECK (duration_minutes >= 0),
    hour_of_day             SMALLINT CHECK (hour_of_day BETWEEN 0 AND 23),
    day_of_week             SMALLINT CHECK (day_of_week BETWEEN 0 AND 6),
    pu_location_id	        SMALLINT REFERENCES silver.dim_zone(zone_id),
    do_location_id          SMALLINT REFERENCES silver.dim_zone(zone_id),
	created_at              TIMESTAMPTZ DEFAULT NOW(),

	PRIMARY KEY (pickup_at, trip_id)
) PARTITION BY RANGE (pickup_at);

CREATE INDEX IF NOT EXISTS idx_fact_trips_pickup_at ON silver.fact_trips (pickup_at);
CREATE INDEX IF NOT EXISTS idx_fact_trips_pu_location ON silver.fact_trips (pu_location_id);
CREATE INDEX IF NOT EXISTS idx_fact_trips_do_location ON silver.fact_trips (do_location_id);
CREATE INDEX IF NOT EXISTS idx_fact_trips_dow_hour ON silver.fact_trips (day_of_week, hour_of_day);
CREATE INDEX IF NOT EXISTS idx_fact_trips_payment_type ON silver.fact_trips (payment_type);

ALTER TABLE silver.fact_trips OWNER TO admin_role;

CREATE TABLE IF NOT EXISTS bronze.etl_file_log (
    log_id              BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    file_name           TEXT NOT NULL UNIQUE,
    file_hash           TEXT,
    processed_at        TIMESTAMPTZ DEFAULT NOW(),
    status              TEXT NOT NULL
);
ALTER TABLE bronze.etl_file_log OWNER TO admin_role;

GRANT USAGE ON SCHEMA bronze, silver, gold TO etl_role;
GRANT CREATE ON SCHEMA bronze TO etl_role;
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA bronze TO etl_role;
ALTER DEFAULT PRIVILEGES FOR ROLE admin_role IN SCHEMA bronze
   GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON TABLES TO etl_role;

GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA silver TO etl_role;
ALTER DEFAULT PRIVILEGES FOR ROLE admin_role IN SCHEMA silver
   GRANT SELECT, INSERT ON TABLES TO etl_role;

GRANT USAGE ON SCHEMA silver, gold TO analyst_role;
GRANT SELECT ON ALL TABLES IN SCHEMA silver TO analyst_role;
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO analyst_role;
ALTER DEFAULT PRIVILEGES FOR ROLE admin_role IN SCHEMA silver
   GRANT SELECT ON TABLES TO analyst_role;
ALTER DEFAULT PRIVILEGES FOR ROLE admin_role IN SCHEMA gold
   GRANT SELECT ON TABLES TO analyst_role;

GRANT USAGE ON SCHEMA gold TO api_role;
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO api_role;
ALTER DEFAULT PRIVILEGES FOR ROLE admin_role IN SCHEMA gold
   GRANT SELECT ON TABLES TO api_role;

DO $$
BEGIN
    INSERT INTO silver.dim_payment_type (payment_type_id, description) VALUES
    (0, 'Tarifa Flex (Flex Fare)'),
    (1, 'Cartão de crédito'),
    (2, 'Dinheiro'),
    (3, 'Sem cobrança'),
    (4, 'Disputa'),
    (5, 'Desconhecido'),
    (6, 'Corrida anulada');
END $$;

DO $$
BEGIN
    INSERT INTO silver.dim_rate_code  (rate_code_id, description) VALUES
    (1, 'Tarifa padrão'),
    (2, 'JFK'),
    (3, 'Newark'),
    (4, 'Nassau ou Westchester'),
    (5, 'Tarifa negociada'),
    (6, 'Corrida em grupo'),
    (99, 'Nulo/desconhecido');
END $$;

DO $$
BEGIN
    INSERT INTO silver.dim_vendor (vendor_id, name) VALUES
    (1, 'Creative Mobile Technologies, LLC'),
    (2, 'Curb Mobility, LLC'),
    (3, 'Myle Technologies Inc'),
    (4, 'Helix');
END $$;

-- =============================================================================
-- FIM DO SCRIPT
-- =============================================================================