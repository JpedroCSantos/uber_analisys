# Análise de Dados de Corridas da cidade de Nova York


Este projeto destina-se à análise de dados de corridas de taxis e limusines, seguindo o desafio técnico descrito em [`docs/PROJECT DOCUMENTATION.md`](docs/PROJECT%20DOCUMENTATION.md). O objetivo é realizar a ingestão, limpeza, transformação e análise de um dataset público para extrair insights valiosos.

##  Estrutura do Projeto

O projeto está organizado da seguinte forma:

```
trip_analysis/
├── app/               # Contém o código-fonte da aplicação
├── data/              # Armazena os datasets brutos e processados
├── docs/              # Documentação do projeto
├── tests/             # Testes unitários e de integração
├── pyproject.toml     # Arquivo de configuração do projeto e dependências
└── Readme.md          # Este arquivo
```

## Execução com Docker (Recomendado)

Pré-requisitos:
- Docker Desktop (ou Docker Engine) e Docker Compose v2 habilitado

1) Crie um arquivo `.env` na raiz do projeto (mínimo necessário):
```bash
# Ambiente
APP_ENV=DEV
LOG_LEVEL=INFO

# Execução do pipeline (sem Postgres por padrão)
EXPORT_TO_DB=false
OUTPUT_FORMAT=csv
OUTPUT_CSV_NAME=gold_trips.csv

# Amostragem para testes
SAMPLE_ENABLED=true
SAMPLE_N=20000
SAMPLE_RANDOM_STATE=42
```

2) (Opcional) Para usar Postgres via Docker/externo, adicione também:
```bash
PG_HOST=your-host
PG_PORT=5432
PG_DATABASE=trip_db
PG_USER=postgres
PG_PASSWORD=your_password

# Parâmetros robustos (opcionais)
APPLICATION_NAME=etl_trips
CONNECT_TIMEOUT=10
SSLMODE=require
KEEPALIVES=1
KEEPALIVES_IDLE=30
KEEPALIVES_INTERVAL=10
KEEPALIVES_COUNT=5
```

3) Suba os serviços:
```bash
docker compose up --build
```

O pipeline é executado dentro do container (equivalente a `python app/main.py`). Os artefatos de saída serão gravados em `data/output/gold/` e os logs em `logs/app.log`. Garanta que os volumes estejam mapeados no `docker-compose.yml` para persistir arquivos no host.

---

## Execução Local sem Docker (Opcional)

Siga os passos abaixo apenas se você pretende executar localmente sem Docker.

### Pré-requisitos (sem Docker)

- Python 3.9+
- Poetry (para gerenciamento de dependências)
- Git

### Instalação (sem Docker)

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/JpedroCSantos/trips_analysis.git
    cd trips_analysis
    ```

2.  **Instale as dependências:**
    O projeto utiliza [Poetry](https://python-poetry.org/) para gerenciar as dependências. Para instalá-las, execute:
    ```bash
    poetry install
    ```

3.  **Ative o ambiente virtual:**
    ```bash
    poetry shell
    ou
    source .venv/scripts/activate
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
    APPLICATION_NAME=etl_trips
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

---

## Execução com Docker (Recomendado)

Pré-requisitos:
- Docker Desktop (ou Docker Engine) e Docker Compose v2 habilitado

1) Crie um arquivo `.env` na raiz do projeto (mínimo necessário):
```bash
# Ambiente
APP_ENV=DEV
LOG_LEVEL=INFO

# Execução do pipeline (sem Postgres por padrão)
EXPORT_TO_DB=false
OUTPUT_FORMAT=csv
OUTPUT_CSV_NAME=gold_trips.csv

# Amostragem para testes
SAMPLE_ENABLED=true
SAMPLE_N=20000
SAMPLE_RANDOM_STATE=42
```

2) (Opcional) Para usar Postgres via Docker/externo, adicione também:
```bash
PG_HOST=your-host
PG_PORT=5432
PG_DATABASE=trip_db
PG_USER=postgres
PG_PASSWORD=your_password

# Parâmetros robustos (opcionais)
APPLICATION_NAME=etl_trips
CONNECT_TIMEOUT=10
SSLMODE=require
KEEPALIVES=1
KEEPALIVES_IDLE=30
KEEPALIVES_INTERVAL=10
KEEPALIVES_COUNT=5
```

3) Suba os serviços:
```bash
docker compose up --build
```

O pipeline é executado dentro do container (equivalente a `python app/main.py`). Os artefatos de saída serão gravados em `data/output/gold/` e os logs em `logs/app.log`. Garanta que os volumes estejam mapeados no `docker-compose.yml` para persistir arquivos no host.

---

## Execução do Pipeline (Resumo)

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

### Consultas SQL das Perguntas de Negócio

As respostas (queries) das perguntas de negócio estão organizadas em `sql/Question 1` a `sql/Question 5`. Consulte essas pastas para ver as consultas em SQL que respondem cada questão do desafio.

## 📊 Dashboard Interativo no Power BI

Este projeto inclui um dashboard interativo no Power BI para visualização dos dados e análises da nossa pipeline de ETL. Para utilizá-lo, siga as instruções abaixo para carregar os dados tratados do seu ambiente local.

Nota: A versão principal deste dashboard está publicada online [aqui](https://app.powerbi.com/view?r=eyJrIjoiYWI2NjM3ODUtMzNlNi00MjFlLThlNzYtYTQ0MDczN2U5ZDdiIiwidCI6IjliOThlYmM3LWRmMTctNDhlOS1iM2ZjLWQ0MjA4ODQ1ZWQxMCJ9). Siga as instruções abaixo apenas se você deseja abrir o arquivo localmente para analisar o modelo de dados ou os dados tratados em sua máquina.

👉 [Abrir dashboard online »](https://app.powerbi.com/view?r=eyJrIjoiYWI2NjM3ODUtMzNlNi00MjFlLThlNzYtYTQ0MDczN2U5ZDdiIiwidCI6IjliOThlYmM3LWRmMTctNDhlOS1iM2ZjLWQ0MjA4ODQ1ZWQxMCJ9)

### 🛠️ Como Usar o Dashboard (Versão Local)

O dashboard `trips_nyc.pbix` já está configurado para ler os arquivos de dados da camada gold do projeto. No entanto, o caminho para os arquivos precisa ser ajustado para o diretório da sua máquina.

Siga estes 3 passos simples:

1. **Abra o Arquivo:**
   - Abra o arquivo `trips_nyc.pbix` no Power BI Desktop.

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

- **Escopo dos Dados**
  - Decisão: limitar a carga a Jan/2023–Jul/2025 do “Yellow Taxi”.
  - Justificativa: volume suficiente para exigir otimização (partições/índices) e ainda viabilizar ciclos rápidos de desenvolvimento (ETL, análises, API/Dashboard).
  - Alternativa: histórico completo (2009–2025) e/ou “Green Taxi” — maior custo/complexidade sem ganho proporcional no aprendizado nesta fase.

- **Hospedagem do Banco (Neon Serverless Postgres)**
  - Decisão: usar o Free Tier da Neon.
  - Justificativa: arquitetura serverless moderna; auto-suspend útil para DEV/estudo; bom free tier.
  - Implicação: limite de armazenamento (~3 GiB) motiva amostragem.

- **Amostragem Mensal (20.000 registros/mês)**
  - Decisão: amostrar 20k corridas/mês de Dez/2022 a Jul/2025.
  - Justificativa: respeita o limite de armazenamento; acelera o ciclo de desenvolvimento; mantém diversidade temporal.

- **Estratégia de Carga (`execute_values` vs `COPY`)**
  - Decisão: `execute_values` como padrão.
  - Justificativa: robusto em nuvem gerenciada (Render/Neon); melhor que `executemany`; independente de FS/search_path/ACLs.
  - Alternativa: `COPY` (mais performático em ambiente ideal) — mantido isolado para uso futuro.

- **Arquitetura (Medallion + Estrela)**
  - Decisão: Bronze (staging), Silver (fato + dimensões), Gold (MVs).
  - Justificativa: separação clara de responsabilidades; leitura analítica otimizada; menor custo de JOINs.

- **Particionamento Mensal Automatizado**
  - Decisão: criar partições de `silver.fact_trips` via aplicação antes da carga.
  - Justificativa: pipeline autocontido; evita falhas por partição ausente; ranges half-open `[from, to)` e checagem via `to_regclass`.

- **Conexão e Transações**
  - Conexão única por execução e commits por lote (10k) no `execute_values` para evitar timeouts e reduzir risco.
  - Conexão robusta: `keepalives`, `connect_timeout`, `sslmode=require`, `application_name` e retry/backoff.

- **Ordem de Carga e Integridade**
  - Dimensões antes de fatos (`silver.dim_zone` antes de `fact_trips`) para evitar violações de FK.

- **Tratamento de Outliers e Dtypes**
  - `trip_distance` filtrada (<= `config.max_trip_distance`, default 300); centralização de `dtypes` e parse em `config.py`.

- **Logging e Retenção Bronze**
  - Logging simples em DEV (`logs/app.log` + console); produção pode usar JSONL.
  - Bronze com TRUNCATE após mover para Silver no contexto deste projeto (portfólio); produção depende de governança/backup.


## Modelo de Dados (resumo)

- `silver.dim_zone(zone_id, borough, zone_name, service_zone)`
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