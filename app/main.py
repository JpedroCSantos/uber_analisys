from pipeline.extract import getDataInCsv, getDataInParquet

PATH = 'data/input'
FILE_NAME = 'yellow_tripdata_2025-01'

df = getDataInParquet(path=PATH, file_name=FILE_NAME)
print(df.shape)

emptyColuns = [colum for colum, value in df.isna().sum().items() if value > 0]
for column in emptyColuns:
    print(f"{column} - {df[column].unique()}")
print(((df['passenger_count'].isna()) & (df['RatecodeID'].isna())).sum())
""" 
    Hipotese 1 - A corrida que tem o passenger_count nAn, poderia ser uma corrida
    de passageiros 0, do tipo entrega.
    Para isso acontecer o RatecodeID da corrida teria de existir na mesma linha para
    essa inferência.

    Resultado: Em todas as linhas que passenger_count é null/nan RatecodeID também é,
    o que invalida a Hipotese levantada.

    SOLUÇÃO: Remover do database qualquer linha que contenha um valor null/nan
"""
initialLen = len(df)
df = df.dropna(subset=emptyColuns)
print(f"Linhas removidas: {initialLen - len(df)}")
print(df.shape)

"""
- Crie novas colunas que serão úteis para a análise, como:
    - `duration_minutes`: Duração da corrida em minutos.
    - `day_of_week`: Dia da semana (ex: Segunda-feira, Terça-feira).
    - `hour_of_day`: A hora em que a corrida começou.

- Crie sua class em python para carregar os dados do banco de dados.
- Crie o schema do seu banco
- Popular o Banco
"""

"""
- Features futuras
    1. Colocar banco online
    2. Consultar dados do banco via python
    3. criar uma aplicação online que vai servir como API para meu banco
    4. Criar uma aplicação que consome os dados desse banco
    5. Criar um dashboard com os dados da analise
"""