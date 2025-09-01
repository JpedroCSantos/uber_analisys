# Desafio Técnico: Análise de Dados de Corridas da Uber

# **Desafio Técnico: Análise de Dados de Corridas da Uber**

## **Contexto do Desafio:**

Você acaba de ser contratado como Engenheiro de Dados em uma consultoria de análise de dados. Nosso novo cliente é uma empresa de transporte por aplicativo que busca otimizar suas operações na cidade de Nova York. Eles nos forneceram um grande volume de dados brutos de corridas e esperam que nossa equipe extraia insights acionáveis.

Sua primeira tarefa é realizar uma análise exploratória profunda, focando na eficiência operacional e no comportamento de motoristas e passageiros. Este projeto testará sua habilidade em todo o ciclo inicial de um projeto de dados: ingestão, limpeza, transformação e análise analítica.

## **Objetivo Principal:**

Processar e analisar um dataset público de corridas para responder a um conjunto de perguntas de negócio críticas. O projeto deve demonstrar proficiência em manipulação de dados com Python/Pandas e, principalmente, na formulação de consultas analíticas complexas com SQL avançado (CTEs e Funções de Janela).

---

## Decisões Técnicas Importantes

### Carga no Postgres

- **Padrão: `execute_values`** (psycopg2.extras). Justificativa:
  - Maior robustez em provedores gerenciados (Render) do que `COPY`.
  - Performance adequada (2–3x melhor que `executemany`).
  - Independente de filesystem/perm item.
- **Alternativa preservada: `COPY FROM STDIN`**:
  - Mantida isolada no `db_class` para ambientes que suportem.
  - Requer autocommit e cuidado com `search_path`.

### Estabilidade de Conexão

- **Conexão única por execução**: o `main.py` usa apenas um `with db_class(...)` para todo o pipeline.
- **Retry com backoff (60s)** e **keepalive**: reduz falhas transitórias no Render.
- **Commit por lote** (10k): transações curtas; menor risco de reset/timeouts.

### Particionamento e Integridade

- **Particionamento mensal** em `silver.fact_trips (pickup_at)`: ranges half-open `[from, to)`.
- **Criação automática** de partições faltantes; verificação via `to_regclass`.
- **Dimensões antes do fato**: `silver.dim_zone` carregada previamente (upsert) para evitar violations de FK.

### Qualidade de Dados

- **Outliers**: `trip_distance` limitada por `MAX_TRIP_DISTANCE` (default 300); evita estouro do tipo `NUMERIC(7,3)`.
- **Nulos críticos**: remoção apenas em colunas essenciais (datas/locais), preservando cobertura e flexibilidade analítica.
- **Centralização de dtypes**: perfis de importação em `config.py` (usecols, parse_dates, dtypes), garantindo consistência.

### Logging

- **DEV**: console + `logs/app.log` (texto simples).
- **PROD**: opção de JSONL e rotação.

---

## Decisões Críticas e Justificativas (Versão Expandida)

1. Escopo dos Dados (2023–2025, Yellow Taxi)
- Foco no período Jan/2023–Jul/2025 para equilibrar volume e agilidade.
- Alternativa (histórico completo/Green) descartada por custo e complexidade no estágio atual.

2. Banco Serverless (Neon – Free Tier)
- Escolha por facilidade de uso e auto-suspend; free tier sem cartão.
- Limite de ~3 GiB influencia o escopo e impõe amostragem.

2.1. Amostragem (20k registros/mês)
- Controle de volume; rapidez de desenvolvimento; diversidade temporal preservada.

3. Carga com `execute_values`
- Padrão por robustez em cloud (Render/Neon); `COPY` mantido como alternativa.

4. Medallion + Estrela
- Bronze (staging), Silver (fato + dimensões), Gold (MVs) para leituras rápidas.

5. Particionamento mensal automático
- Criado na aplicação antes da carga; validação com `to_regclass`; ranges `[from, to)`.

6. Idempotência (arquivos)
- Preferência por mover arquivos landing→processed; no código atual, log transacional + conexão única.

### Retenção na Bronze

- Após a migração bem-sucedida para a Silver, aplicamos `TRUNCATE` na tabela Bronze. Os dados brutos permanecem acessíveis nos arquivos Parquet do projeto; como este é um portfólio com limitação de espaço, evitamos manter cópias duplicadas em disco e no banco. Em produção, a retenção da Bronze deve seguir políticas de auditoria, reprocessamento e custo de armazenamento.

---

## **Fonte de Dados:**

Utilize o dataset público **TLC Trip Record Data**. Recomendo começar com os dados de "Yellow Taxi" de um único mês para manter o escopo gerenciável. Você pode baixar os arquivos em formato Parquet diretamente do site.

## **Fases do Projeto e Requisitos Técnicos:**

### **Fase 1: Extração e Preparação de Dados (Python e Pandas)**

1. **Carregamento:** Use a biblioteca Pandas para carregar o arquivo Parquet em um DataFrame.
2. **Limpeza e Transformação:**
    - Inspecione o dataset em busca de valores nulos e inconsistências. Decida e implemente uma estratégia para tratá-los (ex: remover ou preencher).
    - Verifique e corrija os tipos de dados de cada coluna (ex: `tpep_pickup_datetime` e `tpep_dropoff_datetime` devem ser do tipo `datetime`).
    - Crie novas colunas que serão úteis para a análise, como:
        - `duration_minutes`: Duração da corrida em minutos.
        - `day_of_week`: Dia da semana (ex: Segunda-feira, Terça-feira).
        - `hour_of_day`: A hora em que a corrida começou.

### **Fase 2: Carga e Análise Analítica (SQL Avançado)**

1. **Carga no Banco de Dados:** Carregue o DataFrame limpo e transformado na tabela particionada `silver.fact_trips` via `execute_values` (commit por lote) após garantir o carregamento de `silver.dim_zone` (upsert).
2. **Análise via SQL:** Escreva consultas SQL para responder às seguintes perguntas de negócio. É fundamental que você utilize **CTEs** e **Funções de Janela**.

---

## **Perguntas de Negócio para Avaliação**

Estas são as perguntas que você deve responder usando SQL. Sua capacidade de resolvê-las de forma correta e eficiente será o principal critério de avaliação do projeto.

### **Pergunta 1: Análise de Padrões Temporais**

- Qual é a média de corridas por hora do dia? E nos fins de semana (sábado e domingo) em comparação com os dias de semana?

### **Pergunta 2: Análise de Desempenho dos Motoristas**

- Para cada motorista (`VendorID`), qual é o tempo médio entre o final de uma corrida e o início da próxima? Isso pode nos dar um insight sobre a eficiência ou o tempo ocioso dos motoristas.
    - **Dica:** A função de janela `LAG()` ou `LEAD()` é ideal para resolver este problema.

### **Pergunta 3: Análise de Localização e Demanda**

- Qual o ranking das 5 principais zonas de embarque (`PULocationID`) com base no valor médio da gorjeta (`tip_amount`)? Considere apenas corridas onde o pagamento foi com cartão de crédito.

### **Pergunta 4: Análise de Valor e Distância**

- Calcule a média móvel de 7 dias do valor total arrecadado (`total_amount`). Isso pode ajudar a suavizar as flutuações diárias e identificar tendências de receita.
    - **Dica:** Funções de janela com uma cláusula de frame (ex: `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW`) são perfeitas para isso.

### **Pergunta 5: Identificação de Corridas Relevantes (Problema Clássico de Entrevista)**

- Para cada `PULocationID`, encontre a terceira corrida mais cara (`total_amount`) que partiu daquela zona. Retorne o `PULocationID` e o valor dessa corrida.
    - **Dica:** Use `ROW_NUMBER()` ou `DENSE_RANK()` particionado por zona de embarque e ordenado pelo valor da corrida.

---

## **Entregáveis Esperados:**

1. **Script Python:** Um arquivo `.py` ou um Jupyter Notebook (`.ipynb`) bem documentado contendo todo o processo da Fase 1 (carga, limpeza e transformação dos dados).
2. **Scripts SQL:** Um ou mais arquivos `.sql` contendo as consultas utilizadas para responder a cada uma das perguntas de negócio da Fase 2. Cada consulta deve ser claramente comentada para explicar a lógica utilizada.
3. **Relatório de Respostas:** Um breve documento em Markdown ou PDF resumindo as respostas encontradas para cada pergunta, acompanhado das tabelas ou resultados gerados pelas queries.

### **Critérios de Avaliação:**

- **Qualidade do Código:** Clareza, organização e comentários tanto no script Python quanto nas queries SQL.
- **Correção e Precisão:** As respostas para as perguntas de negócio devem estar corretas.
- **Proficiência em SQL Avançado:** Uso demonstrado e apropriado de CTEs e Funções de Janela para resolver os problemas propostos.
- **Clareza na Comunicação:** A capacidade de apresentar os resultados de forma clara e concisa no relatório final.

---

## Como Executar

1) Configure `.env` (vide Readme) e o Postgres (scripts em `app/sql`).
2) Rode `python app/main.py`. O pipeline:
   - Exporta `dim_zone` (se habilitado)
   - Processa Bronze/Silver
   - Atualiza MVs na Gold

## Troubleshooting (Resumo)

- "relação não existe" em COPY → use `execute_values` (padrão) ou corrija `search_path`/autocommit.
- "nenhuma partição encontrada" → crie a partição mensal `[YYYY-MM-01, YYYY-(MM+1)-01)`.
- FK violations em `dim_zone` → rodar upsert da dimensão antes da carga do fato.
- NUMERIC out of range → tratar outliers (ou ampliar tipo no DB).