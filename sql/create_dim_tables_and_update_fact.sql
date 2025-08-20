-- =============================================================================
-- SCRIPT DE CRIAÇÃO DAS TABELAS DE DIMENSÃO E FATO (VERSÃO FINAL)
-- SGBD: PostgreSQL 15+
-- Schema: silver
-- Projeto: UBER ANALISYS (OLAP)
-- =============================================================================

-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
-- BLOCO 1: CRIAÇÃO DAS TABELAS DE DIMENSÃO ADICIONAIS
--
-- Descrição: Cria as tabelas de dimensão para Vendor, Rate Code e Payment Type.
-- Estas tabelas servirão como "legendas" para os códigos na tabela fato.
-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

-- Tabela de Dimensão para os fornecedores (Vendors).
CREATE TABLE IF NOT EXISTS silver.dim_vendor (
    vendor_id           SMALLINT PRIMARY KEY,
    name                TEXT NOT NULL
);
ALTER TABLE silver.dim_vendor OWNER TO admin_role;

-- Tabela de Dimensão para os códigos de tarifa (Rate Codes).
CREATE TABLE IF NOT EXISTS silver.dim_rate_code (
    rate_code_id        SMALLINT PRIMARY KEY,
    description         TEXT NOT NULL
);
ALTER TABLE silver.dim_rate_code OWNER TO admin_role;

-- Tabela de Dimensão para os tipos de pagamento (Payment Types).
CREATE TABLE IF NOT EXISTS silver.dim_payment_type (
    payment_type_id     SMALLINT PRIMARY KEY,
    description         TEXT NOT NULL
);
ALTER TABLE silver.dim_payment_type OWNER TO admin_role;

DROP TABLE IF EXISTS silver.fact_trips;
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

-- =============================================================================
-- FIM DO SCRIPT
-- =============================================================================