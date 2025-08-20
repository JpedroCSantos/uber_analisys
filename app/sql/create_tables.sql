-- Criação dos schemas e tabelas para o projeto Uber Analysis
-- Arquitetura Medallion: Bronze -> Silver -> Gold

-- =================
-- SCHEMAS
-- =================
CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- =================
-- BRONZE LAYER
-- =================
-- Tabela landing para dados brutos (com tipos flexíveis)
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
    cbd_congestion_fee      TEXT,
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- =================
-- SILVER LAYER
-- =================
-- Tabela dimensão de zonas
CREATE TABLE IF NOT EXISTS silver.dim_zone (
    zone_id       SMALLINT PRIMARY KEY,
    borough       TEXT NOT NULL,
    zone_name     TEXT NOT NULL,
    service_zone  TEXT
);

-- Tabela fato principal (dados limpos e tipados)
CREATE TABLE IF NOT EXISTS silver.fact_trips (
    trip_id                 BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    vendor_id               SMALLINT,
    passenger_count         SMALLINT CHECK (passenger_count >= 0 AND passenger_count <= 6),
    trip_distance           NUMERIC(7,3) CHECK (trip_distance >= 0),
    ratecode_id             SMALLINT,
    store_and_fwd_flag      BOOLEAN,
    payment_type            SMALLINT,
    fare_amount             NUMERIC(10,2) CHECK (fare_amount >= 0),
    extra                   NUMERIC(10,2) CHECK (extra >= 0),
    mta_tax                 NUMERIC(10,2) CHECK (mta_tax >= 0),
    tip_amount              NUMERIC(10,2) CHECK (tip_amount >= 0),
    tolls_amount            NUMERIC(10,2) CHECK (tolls_amount >= 0),
    improvement_surcharge   NUMERIC(10,2) CHECK (improvement_surcharge >= 0),
    congestion_surcharge    NUMERIC(10,2) CHECK (congestion_surcharge >= 0),
    total_amount            NUMERIC(10,2),
    airport_fee             NUMERIC(10,2) CHECK (airport_fee >= 0),
    cbd_congestion_fee      NUMERIC(10,2) CHECK (cbd_congestion_fee >= 0),
    pickup_at               TIMESTAMPTZ NOT NULL,
    dropoff_at              TIMESTAMPTZ NOT NULL,
    duration_minutes        NUMERIC(6,2) CHECK (duration_minutes >= 0),
    hour_of_day             SMALLINT CHECK (hour_of_day BETWEEN 0 AND 23),
    day_of_week             SMALLINT CHECK (day_of_week BETWEEN 0 AND 6),
    pu_location_id          SMALLINT NOT NULL REFERENCES silver.dim_zone(zone_id),
    do_location_id          SMALLINT NOT NULL REFERENCES silver.dim_zone(zone_id),
    created_at              TIMESTAMPTZ DEFAULT NOW()
);

-- =================
-- ÍNDICES (Performance)
-- =================
-- Bronze: índice simples para auditoria
CREATE INDEX IF NOT EXISTS idx_bronze_created_at ON bronze.raw_trips_landing (created_at);

-- Silver: índices para análises típicas
CREATE INDEX IF NOT EXISTS idx_fact_trips_pickup_at ON silver.fact_trips (pickup_at);
CREATE INDEX IF NOT EXISTS idx_fact_trips_pu_location ON silver.fact_trips (pu_location_id);
CREATE INDEX IF NOT EXISTS idx_fact_trips_do_location ON silver.fact_trips (do_location_id);
CREATE INDEX IF NOT EXISTS idx_fact_trips_dow_hour ON silver.fact_trips (day_of_week, hour_of_day);
CREATE INDEX IF NOT EXISTS idx_fact_trips_payment_type ON silver.fact_trips (payment_type);

-- =================
-- COMENTÁRIOS
-- =================
COMMENT ON SCHEMA bronze IS 'Camada Bronze: dados brutos como chegam da fonte';
COMMENT ON SCHEMA silver IS 'Camada Silver: dados limpos, tipados e com qualidade';
COMMENT ON SCHEMA gold IS 'Camada Gold: dados agregados e prontos para consumo';

COMMENT ON TABLE bronze.raw_trips_landing IS 'Landing zone para dados brutos de viagens';
COMMENT ON TABLE silver.dim_zone IS 'Dimensão de zonas geográficas do NYC TLC';
COMMENT ON TABLE silver.fact_trips IS 'Fato principal: viagens limpas e validadas';
