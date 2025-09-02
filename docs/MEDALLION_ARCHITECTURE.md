# Arquitetura Medallion - Implementação

## Visão Geral

Este projeto implementa a arquitetura Medallion para processamento de dados, que consiste em três camadas principais:

- **Bronze**: Dados brutos com validações básicas
- **Silver**: Dados limpos com validações intermediárias
- **Gold**: Dados de alta qualidade para análise de negócios

## Estrutura de Diretórios

```
data/
├── input/                    # Dados de entrada
└── output/
    ├── bronze/              # Camada Bronze
    ├── silver/              # Camada Silver
    └── gold/                # Camada Gold
```

## Configuração

### Variáveis de Ambiente

Configure as seguintes variáveis no seu arquivo `.env`:

```bash
# Caminhos da arquitetura Medallion
OUTPUT_PATH=data/output
BRONZE_PATH=data/output/bronze
SILVER_PATH=data/output/silver
GOLD_PATH=data/output/gold

# Configurações de arquivo
FILENAME=trip_data
DELIMITER=,
```

### Banco de Dados

1) Crie os schemas/tabelas com `app/sql/create_tables.sql` (ou `sql/create_schemas_and_tables.sql`).
2) Garanta indices nas colunas de consulta frequente (ex.: `payment_type`, `pu_location_id`, `do_location_id`, `pickup_at`).
3) Tabela `silver.fact_trips` é particionada por mês (`RANGE` em `pickup_at`). Ranges half-open `[from, to)` evitam sobreposição.

### Conexão e Estabilidade em Cloud

- `db_class` adiciona parâmetros de conexão (keepalive, sslmode, timeouts) e retry com backoff (60s) no `connect_db`.
- Carga com `execute_values` usa commit por lote (10k linhas) para reduzir tempo de transação.


### Configurações de Qualidade por Camada

#### Bronze
- Validação básica
- Colunas obrigatórias: `tpep_pickup_datetime`, `tpep_dropoff_datetime`
- Permite duplicatas

#### Silver
- Validação intermediária
- Colunas obrigatórias: + `PULocationID`, `DOLocationID`
- Não permite duplicatas
- Threshold de valores nulos: 10%

#### Gold
- Validação rigorosa
- Colunas obrigatórias: + `total_amount`
- Não permite duplicatas
- Threshold de valores nulos: 0%
- Regras de negócio aplicadas

## Uso

### Funções de Load

```python
from pipeline.load import load_bronze, load_silver, load_gold

# Salvar na camada Bronze
load_bronze(df, settings)

# Salvar na camada Silver
load_silver(df, settings)

# Salvar na camada Gold
load_gold(df, settings)

# Ou usar a função genérica
from pipeline.load import load_csv
load_csv(df, settings, "bronze")
load_csv(df, settings, "silver")
load_csv(df, settings, "gold")
```

### Pipeline Completo

O arquivo `main.py` demonstra um pipeline completo com **conexão única por execução**:

1. **Extração**: Carrega dados do arquivo Parquet
2. **Bronze**: Leitura/mapeamento de colunas (mapeamento de nomes padronizado)
3. **Silver**: Derivações (`duration_minutes`, `day_of_week`, `hour_of_day`), tratamento de outliers (ex.: `trip_distance`), remoção de nulos críticos, mapeamento final de nomes
4. **Carga**: `execute_values` (padrão) com commit por lote; partições mensais criadas automaticamente se faltarem
5. **Gold**: Refresh de materialized views

## Nomenclatura de Arquivos

Os arquivos são salvos com sufixos indicando a camada:
- `trips_data_bronze.csv`
- `trips_data_silver.csv`
- `trips_data_gold.csv`

## Benefícios

- **Rastreabilidade**: Cada camada representa um nível de qualidade
- **Flexibilidade**: Pode-se usar dados de qualquer camada conforme necessário
- **Escalabilidade**: Fácil adicionar novas validações ou camadas
- **Manutenibilidade**: Separação clara de responsabilidades

---

## Decisões Críticas

- **Carga via execute_values (padrão)**: mais robusta em ambientes gerenciados; `COPY` preservado como alternativa futura.
- **Conexão única**: reduz churn de conexões, evita erros de “not yet accepting connections”.
- **Commit por lote**: transações curtas; mais estável no Render.
- **Particionamento mensal**: evita bloat, facilita autovacuum e consultas por período.
- **Dim antes de fato**: evita violations de FK.
- **Tratamento de outliers**: evita estouro de tipos NUMERIC;
- **Centralização de dtypes/parse**: garante consistência e economia de memória.

### Versão Expandida

1) Escopo dos dados (2023–2025, Yellow Taxi)
- Foco em Jan/2023–Jul/2025 para balancear volume e agilidade.
- Alternativas amplas (2009–2025, Green Taxi) descartadas por custo/complexidade.

2) Banco serverless (Neon, Free Tier)
- Escolhida pela facilidade, auto-suspend e free tier generoso.
- Limite de ~3 GiB demanda amostragem controlada.

2.1) Amostragem estratificada (20k/mês)
- Mantém diversidade temporal e reduz custo de armazenamento/execução.

3) Carga `execute_values` (padrão) vs `COPY`
- `execute_values`: robusto em nuvem; `COPY` fica como alternativa em ambientes ideais.

4) Medallion + Estrela
- Bronze (staging), Silver (fato+dimensões), Gold (MVs) para otimizar leitura.

5) Particionamento automático
- App cria partições mensais antes da carga; ranges `[from, to)`.

6) Idempotência
- Preferir mover arquivos processados landing→processed (e/ou log transacional) para reprocessos seguros.
