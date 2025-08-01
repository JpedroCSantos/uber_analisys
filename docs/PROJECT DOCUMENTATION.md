# Desafio Técnico: Análise de Dados de Corridas da Uber

# **Desafio Técnico: Análise de Dados de Corridas da Uber**

## **Contexto do Desafio:**

Você acaba de ser contratado como Engenheiro de Dados em uma consultoria de análise de dados. Nosso novo cliente é uma empresa de transporte por aplicativo que busca otimizar suas operações na cidade de Nova York. Eles nos forneceram um grande volume de dados brutos de corridas e esperam que nossa equipe extraia insights acionáveis.

Sua primeira tarefa é realizar uma análise exploratória profunda, focando na eficiência operacional e no comportamento de motoristas e passageiros. Este projeto testará sua habilidade em todo o ciclo inicial de um projeto de dados: ingestão, limpeza, transformação e análise analítica.

## **Objetivo Principal:**

Processar e analisar um dataset público de corridas para responder a um conjunto de perguntas de negócio críticas. O projeto deve demonstrar proficiência em manipulação de dados com Python/Pandas e, principalmente, na formulação de consultas analíticas complexas com SQL avançado (CTEs e Funções de Janela).

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

1. **Carga no Banco de Dados:** Carregue o DataFrame limpo e transformado para uma tabela em um banco de dados PostgreSQL local. Nomeie a tabela como `uber_trips`.
2. **Análise via SQL:** Escreva consultas SQL para responder às seguintes perguntas de negócio. É fundamental que você utilize **CTEs (cláusula `WITH`)** para organizar a lógica e **Funções de Janela (`OVER (PARTITION BY... ORDER BY...)` )** sempre que forem a solução mais eficiente e elegante.

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