-- =============================================================================
-- SCRIPT DE CRIAÇÃO DAS TABELAS DE DIMENSÃO E FATO (VERSÃO FINAL)
-- SGBD: PostgreSQL 15+
-- Schema: silver
-- Projeto: TRIPS ANALYSIS (OLAP)
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
-- =============================================================================
-- FIM DO SCRIPT
-- =============================================================================