# Análise de Dados de Corridas da Uber

Este projeto destina-se à análise de dados de corridas da Uber, seguindo o desafio técnico descrito em [`docs/PROJECT DOCUMENTATION.md`](docs/PROJECT%20DOCUMENTATION.md). O objetivo é realizar a ingestão, limpeza, transformação e análise de um dataset público para extrair insights valiosos.

##  Estrutura do Projeto

O projeto está organizado da seguinte forma:

```
uber_analisys/
├── app/               # Contém o código-fonte da aplicação
├── data/              # Armazena os datasets brutos e processados
├── docs/              # Documentação do projeto
├── tests/             # Testes unitários e de integração
├── pyproject.toml     # Arquivo de configuração do projeto e dependências
└── Readme.md          # Este arquivo
```

## Configuração do Ambiente

Siga os passos abaixo para configurar o ambiente de desenvolvimento local.

### Pré-requisitos

- Python 3.9+
- Poetry (para gerenciamento de dependências)
- Git

### Instalação

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/JpedroCSantos/uber_analisys.git
    cd uber_analisys
    ```

2.  **Instale as dependências:**
    O projeto utiliza [Poetry](https://python-poetry.org/) para gerenciar as dependências. Para instalá-las, execute:
    ```bash
    poetry install
    ```

3.  **Ative o ambiente virtual:**
    ```bash
    poetry shell
    ```

4.  **Variáveis de ambiente (.env):**
    Crie um arquivo `.env` na raiz com as credenciais do Postgres e parâmetros padrão (exemplo):
    ```bash
    APP_ENV=DEV
    LOG_LEVEL=INFO
    
    # Postgres (Render/Cloud)
    PG_HOST=your-host
    PG_PORT=5432
    PG_DATABASE=trip_db
    PG_USER=postgres
    PG_PASSWORD=your_password
    
    # Conexão robusta (opcional)
    APPLICATION_NAME=etl_uber
    CONNECT_TIMEOUT=10
    SSLMODE=require
    KEEPALIVES=1
    KEEPALIVES_IDLE=30
    KEEPALIVES_INTERVAL=10
    KEEPALIVES_COUNT=5
    
    # Dimensão de zonas
    EXPORT_DIM_TABLE=true
    DIM_TABLE_ZONES_PATH=docs
    TABLE_ZONES_FILE=taxi_zone_lookup
    DIM_TABLE_DTYPES={"LocationID":"Int64","Borough":"string","Zone":"string","service_zone":"string"}
    
    # Execução do pipeline
    EXPORT_TO_DB=false              # padrão: gerar CSV (sem precisar de Postgres)
    OUTPUT_CSV_NAME=gold_trips.csv  # nome do CSV salvo em data/output/gold
    OUTPUT_FORMAT=csv               # csv | parquet (padrão csv)
    
    # Amostragem para testes (quando true, exporta apenas SAMPLE_N linhas)
    SAMPLE_ENABLED=true
    SAMPLE_N=20000
    SAMPLE_RANDOM_STATE=42
    ```

5.  **Banco de dados (DDL):**
    Execute os scripts em `app/sql/create_tables.sql` e, opcionalmente, `sql/create_schemas_and_tables.sql` para criar schemas e tabelas (Bronze/Silver/Gold). A tabela fato `silver.fact_trips` é particionada por mês em `pickup_at`.

---

## Execução do Pipeline

O arquivo `app/main.py` orquestra todo o fluxo:

1) (Somente quando `EXPORT_TO_DB=true`) exporta a dimensão `silver.dim_zone` (upsert) a partir de `docs/taxi_zone_lookup.csv` se `EXPORT_DIM_TABLE=true`.
2) Processa os arquivos Parquet do diretório `data/input` (podado via `list_files`).
3) Bronze: leitura + mapeamento de colunas.
4) Silver: derivação de colunas (`duration_minutes`, `hour_of_day`, `day_of_week`), tratamento de valores críticos e remoção de nulos críticos.
5) Salva um CSV pronto para consumo em `data/output/gold/gold_trips.csv`.
6) (Opcional) Se `EXPORT_TO_DB=true`, carrega no Postgres via `execute_values` (commit por lote) e executa refresh das MVs na Gold.

Para rodar:
```bash
python app/main.py
```

### Fluxos suportados

- **Padrão (sem Postgres)**:
  - Clone o repo, configure o ambiente e rode `python app/main.py`.
  - O arquivo tratado estará em `data/output/gold/gold_trips.csv` (ou `.parquet` se `OUTPUT_FORMAT=parquet`).
  - Se houver múltiplos arquivos Parquet, a saída é construída em modo append. Para CSV: cabeçalho apenas na primeira gravação. Para Parquet: concatena e regrava o arquivo.
  - Para acelerar testes, use `SAMPLE_ENABLED=true` e ajuste `SAMPLE_N`.

- **Avançado (com Postgres)**:
  - Defina no `.env` as variáveis do banco (`PG_HOST`, `PG_PORT`, `PG_DATABASE`, `PG_USER`, `PG_PASSWORD`) e `EXPORT_TO_DB=true`.
  - Rode `python app/main.py` para realizar a ingestão na Silver e o refresh das MVs na Gold.

## 📊 Dashboard Interativo no Power BI

Este projeto inclui um dashboard interativo no Power BI para visualização dos dados e análises da nossa pipeline de ETL. Para utilizá-lo, siga as instruções abaixo para carregar os dados tratados do seu ambiente local.

Nota: A versão principal deste dashboard está publicada online [aqui](LINK_DO_DASHBOARD){:target="_blank"}. Siga as instruções abaixo apenas se você deseja abrir o arquivo localmente para analisar o modelo de dados ou os dados tratados em sua máquina.

### 🛠️ Como Usar o Dashboard (Versão Local)

O dashboard `uber_analisys.pbix` já está configurado para ler os arquivos de dados da camada gold do projeto. No entanto, o caminho para os arquivos precisa ser ajustado para o diretório da sua máquina.

Siga estes 3 passos simples:

1. **Abra o Arquivo:**
   - Abra o arquivo `uber_analisys.pbix` no Power BI Desktop.

2. **Abra o Editor de Consultas:**
   - Na faixa de opções "Página Inicial", clique em "Transformar dados". Isso abrirá o Editor do Power Query.

3. **Edite o Caminho do Projeto:**
   - No painel "Consultas" à esquerda, procure e clique na consulta `pCaminhoProjeto`.
   - Na barra de fórmulas, você verá o caminho atual.
   - Edite o valor atual na barra de fórmulas para o caminho completo do seu projeto na sua máquina.

   Exemplo de como o caminho deve ficar:

   ```
   C:\Users\NomeDoUsuario\CaminhoDoProjeto\
   ```

   Importante: Certifique-se de que o caminho termine com uma barra invertida `\` (ou uma barra normal `/`).

4. **Carregue os Dados:**
   - Após editar o caminho, vá para a faixa de opções "Página Inicial" e clique em "Fechar e Aplicar". O Power BI irá recarregar todos os dados a partir dos arquivos locais no caminho que você acabou de definir.

### Scripts SQL (modo com Postgres)

1. Estrutura base e permissões:
   - Execute `sql/create_db_structure.sql` (unifica criação de roles, schemas, tabelas base e tabela de log, e concede `admin_role` ao usuário atual).
2. Tabelas de dimensão adicionais e redefinição da fato:
   - Execute `sql/create_dim_tables_and_update_fact.sql`.
3. População de dimensões auxiliares:
   - Execute `sql/INSERTS_DIM_TABLES.sql`.

---

## Decisões Críticas e Justificativas

- **Carga via `execute_values` como padrão**: `COPY` é mais rápido em ambientes ideais, mas em provedores gerenciados (Render) observamos falhas e limitações (schema/search_path, permissões de arquivo, transações). `execute_values` é robusto, performático (2–3x mais rápido que `executemany`) e independente de FS.

- **`COPY` isolado e opcional**: Mantido em `db_class` como alternativa (`_load_with_copy_from_stdin`), não chamado por padrão. Permite voltar caso o ambiente suporte.

- **Conexão única por execução**: O `main.py` usa um único `with db_class(...)` para todo o pipeline (dimensão + Bronze + Silver + refresh). Evita “connection churn” e reduz erros de “database not yet accepting connections”.

- **Commits por lote**: Em `execute_values`, cada batch (10k) realiza commit. Mantém transações curtas, reduzindo risco de reset/timeout no provedor.

- **Conexão robusta**: Adicionados `keepalives`, `connect_timeout`, `sslmode=require`, `application_name` e retry com backoff (60s) no `connect_db` para estabilidade em cloud.

- **Particionamento mensal**: `silver.fact_trips` particionada por mês em `pickup_at`. `_handle_partitioning` cria partições faltantes com ranges half-open `[from, to)` e valida existência via `to_regclass`. Evita sobreposição e falhas de roteamento.

- **Ordem de carga (Dim antes de Fato)**: `silver.dim_zone` é populada antes do fato, eliminando violações de FK (`pu/do_location_id`).

- **Tratamento de outliers**: Para `trip_distance` padronizamos limpeza (ex.: `<= config.max_trip_distance`, default 300). Se necessário, o tipo pode ser alterado no Postgres.

- **Centralização de dtypes/parse**: `config.py` define perfis de importação (usecols, parse_dates, dtypes), garantindo consistência entre Bronze e Silver e reduzindo I/O.

- **Logging simples em DEV**: `app/config/logging.py` cria sempre `logs/app.log` e console; produção pode usar JSONL.

- **Bronze com TRUNCATE após carga**: após migrar com sucesso os dados para a Silver, executamos `TRUNCATE` na Bronze. Como os dados brutos já estão disponíveis em arquivos Parquet no repositório e este é um projeto de portfólio com restrição de espaço, optamos por não manter cópias redundantes no banco. Em ambientes produtivos, a retenção de Bronze deve seguir a política de governança/backup.

---

## Decisões Críticas e Justificativas (Versão Expandida)
Esta seção detalha as principais decisões arquiteturais e de implementação, alternativas consideradas e razões da escolha.

1. Escopo dos Dados: Foco em 2023–2025 vs. Histórico Completo
- **Decisão**: limitar a carga a Jan/2023–Jul/2025 do “Yellow Taxi”.
- **Justificativa**: volume suficiente para exigir otimização (partições/índices) e ainda viabilizar ciclos rápidos de desenvolvimento (ETL, análises, API/Dashboard).
- **Alternativa**: histórico completo (2009–2025) e/ou “Green Taxi” — descartado por elevar custo e complexidade sem ganho proporcional no aprendizado nesta fase.

2. Hospedagem do Banco de Dados: Neon Serverless Postgres
- **Decisão**: usar o Free Tier da Neon.
- **Justificativa**: arquitetura serverless moderna; free tier generoso; auto-suspend facilita ambientes de estudo/desenvolvimento.
- **Implicação**: limite de armazenamento (~3 GiB) impacta o escopo e motiva amostragem.

2.1. Amostragem Mensal (20.000 registros/mês)
- **Decisão**: amostrar 20k corridas/mês de Dez/2022 a Jul/2025.
- **Justificativa**: respeita limite do free tier; acelera o ciclo de desenvolvimento; mantém diversidade temporal para análises YoY relevantes.

3. Estratégia de Carga: `execute_values` vs. `COPY`
- **Decisão**: `execute_values` como padrão.
- **Justificativa**: robusto em nuvem gerenciada (Render/Neon); melhor que `executemany`; independente de FS/search_path/ACLs.
- **Alternativa**: `COPY` (mais performático em ambiente ideal) — mantido isolado no código para uso futuro.

4. Arquitetura: Medallion + Esquema Estrela (na Silver)
- **Decisão**: Bronze (staging), Silver (fato + dimensões), Gold (MVs).
- **Justificativa**: separação clara de responsabilidades; otimização de leitura analítica; menor custo de JOINs.

5. Particionamento Mensal Automatizado
- **Decisão**: criar partições de `silver.fact_trips` via aplicação antes da carga.
- **Justificativa**: pipeline autocontido e explícito; evita falhas por partição ausente.
- **Alternativa**: jobs/trigger no DB (pg_cron/PLpgSQL) — maior complexidade/baixo ganho neste escopo.

6. Idempotência do Pipeline: movimentação de arquivos
- **Decisão**: preferir mover arquivos processados de landing → processed (design recomendado).
- **Justificativa**: simples/visual; evita reprocessamento; mantém landing limpa.
- **Alternativa**: log no banco — mais robusta; no código atual, mantemos uma tabela de log e conexão única; pode evoluir para movimentação física.


## Modelo de Dados (resumo)

- `silver.dim_zone(zone_id PK, borough, zone_name, service_zone)`
- `silver.fact_trips` (particionada por mês em `pickup_at`):
  - Chaves e dimensões: `vendor_id`, `pu_location_id`, `do_location_id`, `payment_type`, `ratecode_id`, `store_and_fwd_flag`
  - Métricas: `trip_distance`, `fare_amount`, `tip_amount`, `tolls_amount`, `total_amount`, etc.
  - Data/hora derivadas: `pickup_at`, `dropoff_at`, `duration_minutes`, `hour_of_day`, `day_of_week`
  - FKs: `pu_location_id`/`do_location_id` → `dim_zone(zone_id)`

---

## Troubleshooting

- “relação não existe” em COPY: usar `execute_values` (padrão) ou garantir `SET search_path` e autocommit fora de transação.
- “nenhuma partição encontrada”: crie a partição mensal ausente (ex.: 2024_12) com range `[YYYY-MM-01, YYYY-(MM+1)-01)`.
- “FK violation dim_zone”: rode primeiro o upsert da dimensão (ou DEFERRABLE como último recurso).
- “numeric out of range (7,3)”: ajuste outliers na transformação ou altere o tipo no Postgres.
