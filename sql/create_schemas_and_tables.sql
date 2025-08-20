-- =============================================================================
-- SCRIPT DE CONFIGURAÇÃO DE BANCO DE DADOS ANALÍTICO (DATA WAREHOUSE)
-- SGBD: PostgreSQL 15+
-- Arquitetura: Medallion (Bronze, Silver, Gold)
-- Projeto: Análise de Corridas de Táxi de Nova York (OLAP)
-- Autor: João Pedro Santos + Gemini (Atuando como Engenheiro de Dados Sênior/DBA)
-- =============================================================================

-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
-- BLOCO 1: CRIAÇÃO DE ROLES (PAPÉIS) E GRUPO DE ADMINISTRAÇÃO
--
-- Descrição: Criação de um papel de administrador para ser o dono dos objetos
-- e os papéis específicos da aplicação (ETL, Analista, API), seguindo o
-- Princípio do Menor Privilégio.
-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

-- Comentário: Cria um papel para ser o dono de todos os objetos do banco de dados.
-- Isso evita que os papéis de aplicação sejam donos, o que é uma boa prática de segurança.
CREATE ROLE admin_role WITH
  NOLOGIN
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE
  INHERIT
  NOREPLICATION
  CONNECTION LIMIT -1;

-- Comentário: Papel para os processos de ETL. Terá permissões de escrita nas camadas bronze e silver.
CREATE ROLE etl_role WITH
  NOLOGIN
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE
  INHERIT
  NOREPLICATION
  CONNECTION LIMIT -1;

-- Comentário: Papel para os Analistas de Dados. Terá permissão apenas de leitura nas camadas silver e gold.
CREATE ROLE analyst_role WITH
  NOLOGIN
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE
  INHERIT
  NOREPLICATION
  CONNECTION LIMIT -1;

-- Comentário: Papel para a API de negócio. Terá permissão apenas de leitura na camada gold.
CREATE ROLE api_role WITH
  NOLOGIN
  NOSUPERUSER
  NOCREATEDB
  NOCREATEROLE
  INHERIT
  NOREPLICATION
  CONNECTION LIMIT -1;


-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
-- BLOCO 2: CRIAÇÃO DOS SCHEMAS DA ARQUITETURA MEDALLION
--
-- Descrição: Cria os schemas lógicos para as camadas Bronze, Silver e Gold.
-- Todos os schemas pertencerão ao `admin_role`.
-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

-- Comentário: Schema 'bronze' para a "landing zone" dos dados brutos.
CREATE SCHEMA IF NOT EXISTS bronze AUTHORIZATION admin_role;

-- Comentário: Schema 'silver' para os dados limpos e modelados (Star Schema).
CREATE SCHEMA IF NOT EXISTS silver AUTHORIZATION admin_role;

-- Comentário: Schema 'gold' para os dados agregados e prontos para consumo.
CREATE SCHEMA IF NOT EXISTS gold AUTHORIZATION admin_role;


-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
-- BLOCO 3: CRIAÇÃO DAS TABELAS
--
-- Descrição: Criação das estruturas de tabelas dentro dos schemas apropriados.
-- Inclui tabelas na camada Bronze (exemplo), e as tabelas Fato/Dimensão
-- na camada Silver, conforme especificado.
-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

-- Comentário: Exemplo de tabela na camada Bronze. Colunas genéricas (TEXT)
-- para garantir que a carga de dados brutos nunca falhe por tipo de dado.
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


-- Comentário: Tabela de Dimensão para as localidades (bairros/zonas) de NY.
-- Esta tabela reside na camada Silver, pois contém dados mestres e limpos.
CREATE TABLE IF NOT EXISTS silver.dim_zone (
  zone_id       SMALLINT PRIMARY KEY,
  borough       TEXT NOT NULL,
  zone_name     TEXT NOT NULL
);
ALTER TABLE silver.dim_zone OWNER TO admin_role;

-- Comentário: Tabela Fato principal, contendo os dados de cada corrida.
-- A tabela é particionada por RANGE na coluna `pickup_at` para otimizar
-- consultas baseadas em períodos de tempo, uma prática essencial para OLAP.
CREATE TABLE IF NOT EXISTS silver.fact_trips (
  trip_id                 BIGINT GENERATED ALWAYS AS IDENTITY,
  vendor_id               SMALLINT,
  passenger_count         SMALLINT,
  trip_distance           NUMERIC(7,3),
  ratecode_id             SMALLINT,
  store_and_fwd_flag      BOOLEAN,
  payment_type            SMALLINT,
  fare_amount             NUMERIC(10,2),
  extra                   NUMERIC(10,2),
  mta_tax                 NUMERIC(10,2),
  tip_amount              NUMERIC(10,2),
  tolls_amount            NUMERIC(10,2),
  improvement_surcharge   NUMERIC(10,2),
  congestion_surcharge    NUMERIC(10,2),
  total_amount            NUMERIC(10,2),
  airport_fee			  NUMERIC(10,2),
  pickup_at               TIMESTAMPTZ NOT NULL,
  dropoff_at              TIMESTAMPTZ,
  duration_minutes        NUMERIC(6,2),
  hour_of_day             SMALLINT,
  day_of_week             SMALLINT,
  pu_location_id          SMALLINT REFERENCES silver.dim_zone(zone_id),
  do_location_id          SMALLINT REFERENCES silver.dim_zone(zone_id),
  cbd_congestion_fee      NUMERIC(10,2)
) PARTITION BY RANGE (pickup_at);
ALTER TABLE silver.fact_trips OWNER TO admin_role;

-- Comentário: Exemplo de criação de uma partição para o mês de Janeiro de 2025.
-- Novas partições devem ser criadas antes que dados do período correspondente cheguem.
-- A automação da criação de partições é uma prática recomendada em produção.
CREATE TABLE IF NOT EXISTS silver.fact_trips_2025_01 PARTITION OF silver.fact_trips
    FOR VALUES FROM ('2025-01-01 00:00:00+00') TO ('2025-02-01 00:00:00+00');
ALTER TABLE silver.fact_trips_2025_01 OWNER TO admin_role;


-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
-- BLOCO 4: CRIAÇÃO DE VIEWS E TABELAS MATERIALIZADAS (CAMADA GOLD)
--
-- Descrição: Criação de objetos na camada Gold para servir dados pré-agregados
-- a dashboards e APIs, garantindo alta performance de leitura.
-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

-- -- Comentário: View Materializada que resume o total de corridas e o faturamento
-- -- por dia, bairro de partida e tipo de pagamento. Ideal para um dashboard de resumo diário.
-- CREATE MATERIALIZED VIEW IF NOT EXISTS gold.daily_summary_by_borough AS
-- SELECT
--     DATE_TRUNC('day', ft.pickup_at) AS trip_day,
--     dz.borough,
--     ft.payment_type,
--     COUNT(ft.trip_id) AS total_trips,
--     SUM(ft.total_amount) AS total_revenue,
--     AVG(ft.trip_distance) AS avg_distance
-- FROM
--     silver.fact_trips ft
-- JOIN
--     silver.dim_zone dz ON ft.pu_location_id = dz.zone_id
-- GROUP BY
--     1, 2, 3
-- ORDER BY
--     1, 2;
-- ALTER MATERIALIZED VIEW gold.daily_summary_by_borough OWNER TO admin_role;

-- -- Comentário: É necessário criar um índice na view materializada para otimizar o acesso.
-- CREATE UNIQUE INDEX IF NOT EXISTS idx_daily_summary_by_borough ON gold.daily_summary_by_borough (trip_day, borough, payment_type);


-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||
-- BLOCO 5: CONCESSÃO DE PERMISSÕES (GRANTS)
--
-- Descrição: Aplica as permissões definidas para cada papel nos schemas e tabelas.
-- Utiliza "ALTER DEFAULT PRIVILEGES" para garantir que permissões sejam
-- aplicadas automaticamente a futuros objetos criados pelo `admin_role`.
-- |||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||

-- --- Permissões para o etl_role ---

-- Comentário: Permite que o ETL acesse os três schemas.
GRANT USAGE ON SCHEMA bronze, silver, gold TO etl_role;

-- Comentário: Permite que o ETL crie tabelas no schema bronze (ex: para novas fontes de dados brutos).
GRANT CREATE ON SCHEMA bronze TO etl_role;

-- Comentário: Permissão total nas tabelas do schema bronze.
GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA bronze TO etl_role;
ALTER DEFAULT PRIVILEGES FOR ROLE admin_role IN SCHEMA bronze
   GRANT SELECT, INSERT, UPDATE, DELETE, TRUNCATE ON TABLES TO etl_role;

-- Comentário: Permissão de escrita (INSERT) e leitura (SELECT) nas tabelas do schema silver.
GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA silver TO etl_role;
ALTER DEFAULT PRIVILEGES FOR ROLE admin_role IN SCHEMA silver
   GRANT SELECT, INSERT ON TABLES TO etl_role;

-- --- Permissões para o analyst_role ---

-- Comentário: Permite que o analista acesse os schemas silver e gold.
GRANT USAGE ON SCHEMA silver, gold TO analyst_role;

-- Comentário: Permissão de apenas leitura (SELECT) nas tabelas e views dos schemas silver e gold.
GRANT SELECT ON ALL TABLES IN SCHEMA silver TO analyst_role;
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO analyst_role;

-- Comentário: Garante que o analista terá acesso de leitura a novas tabelas/views futuras.
ALTER DEFAULT PRIVILEGES FOR ROLE admin_role IN SCHEMA silver
   GRANT SELECT ON TABLES TO analyst_role;
ALTER DEFAULT PRIVILEGES FOR ROLE admin_role IN SCHEMA gold
   GRANT SELECT ON TABLES TO analyst_role;


-- --- Permissões para o api_role ---

-- Comentário: Permite que a API acesse o schema gold.
GRANT USAGE ON SCHEMA gold TO api_role;

-- Comentário: Permissão de apenas leitura (SELECT) nas views e tabelas do schema gold.
GRANT SELECT ON ALL TABLES IN SCHEMA gold TO api_role;

-- Comentário: Garante que a API terá acesso de leitura a novas views/tabelas no schema gold.
ALTER DEFAULT PRIVILEGES FOR ROLE admin_role IN SCHEMA gold
   GRANT SELECT ON TABLES TO api_role;


-- =============================================================================
-- FIM DO SCRIPT
-- =============================================================================