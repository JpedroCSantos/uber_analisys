CREATE TABLE bronze.etl_file_log (
    log_id              BIGINT PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
    file_name           TEXT NOT NULL UNIQUE,
    file_hash           TEXT, -- Opcional, para verificar se o conteúdo mudou
    processed_at        TIMESTAMPTZ DEFAULT NOW(),
    status              TEXT NOT NULL -- Ex: 'success', 'failed'
);