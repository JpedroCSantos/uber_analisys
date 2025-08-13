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
FILENAME=uber_data
DELIMITER=,
```

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

O arquivo `main.py` demonstra um pipeline completo:

1. **Extração**: Carrega dados do arquivo Parquet
2. **Bronze**: Aplica transformações básicas
3. **Silver**: Aplica validações intermediárias
4. **Gold**: Aplica validações rigorosas e limpeza final

## Nomenclatura de Arquivos

Os arquivos são salvos com sufixos indicando a camada:
- `uber_data_bronze.csv`
- `uber_data_silver.csv`
- `uber_data_gold.csv`

## Benefícios

- **Rastreabilidade**: Cada camada representa um nível de qualidade
- **Flexibilidade**: Pode-se usar dados de qualquer camada conforme necessário
- **Escalabilidade**: Fácil adicionar novas validações ou camadas
- **Manutenibilidade**: Separação clara de responsabilidades
