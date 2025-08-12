import pandas as pd
import functools
import os
from loguru import logger
from config.config import Settings

def handle_io_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception("ERRO INESPERADO: Uma falha não prevista ocorreu durante a execução.", backtrace=False)
            raise e
    return wrapper

@handle_io_errors
def get_columns_with_nan(df: pd.DataFrame) -> list:
    """
    Recebe um dataframe e retorna uma lista com as colunas que possuem valores NaN.

    Args:
        df (pd.DataFrame): O DataFrame a ser processado.

    Returns:
        list: Uma lista contendo os nomes das colunas com valores NaN.
    """
    logger.info(f"Iniciando contagem de valores NaN nas colunas do dataframe.")
    empty_columns = [colum for colum, value in df.isna().sum().items() if value > 0]
    logger.info(f"Colunas com valores NaN: {empty_columns}")

    return empty_columns


@handle_io_errors
def remove_nan_values_in_columns(coluns: list, df: pd.DataFrame) -> pd.DataFrame:
    """
    Recebe uma lista de colunas e remove os valores NaN em um dataframe nas colunas especificadas.

    Args:
        coluns (list): Uma lista de nomes de colunas.
        df (pd.DataFrame): O DataFrame a ser processado.

    Returns:
        pd.DataFrame: Um DataFrame do Pandas contendo os dados processado.
    """
    logger.info(f"Iniciando remoção de valores NaN nas colunas: {coluns}")
    initialLen = len(df)
    df = df.dropna(subset=coluns)
    logger.success(f"Linhas removidas: {initialLen - len(df)}")

    return df

@handle_io_errors
def treat_critical_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recebe um dataframe e trata as colunas críticas.

    Args:
        df (pd.DataFrame): O DataFrame a ser processado.

    Returns:
        pd.DataFrame: Um DataFrame do Pandas contendo os dados processado.
    """
    logger.info(f"Iniciando tratamento de colunas críticas.")
    df['store_and_fwd_flag'] = (
        df['store_and_fwd_flag']
        .map({'Y': True, 'N': False})
        .astype('boolean')
    )
    logger.success(f"Colunas tratadas com sucesso.")

    return df

@handle_io_errors
def treat_critical_values(df: pd.DataFrame, config: Settings) -> pd.DataFrame:
    """
    Recebe um dataframe e trata colunas que possuem valores críticos e incoerentes.

    Args:
        df (pd.DataFrame): O DataFrame a ser processado.

    Returns:
        pd.DataFrame: Um DataFrame do Pandas contendo os dados processado.
    """
    logger.info(f"Iniciando tratamento de valores críticos e incoerentes.")
    df['passenger_count'] = (
        pd.to_numeric(df['passenger_count'], errors='coerce')
        .where(lambda s: s.between(1, 5))
        .astype('Int64')
    )
    df['trip_distance'] = (
        pd.to_numeric(df['trip_distance'], errors='coerce')
        .where(lambda s: s > 0)
        .astype('float32')
    )
    df['duration_minutes'] = (
        pd.to_numeric(df['duration_minutes'], errors='coerce')
        .where(lambda s: s > 0)
        .astype('float32')
    )
    for column in config.amount_columns:
        df[column] = (
            pd.to_numeric(df[column], errors='coerce')
            .where(lambda s: s >= 0)
            .astype('float32')
        )
    logger.success(f"Colunas tratadas com sucesso.")

    return df

@handle_io_errors
def insert_new_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Recebe um dataframe e insere novas colunas.

    Args:
        df (pd.DataFrame): O DataFrame a ser processado.

    Returns:
        pd.DataFrame: Um DataFrame do Pandas contendo os dados processado.
    """
    logger.info(f"Iniciando inserção de novas colunas.")
    df['duration_minutes'] = (
        (df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime'])
        .dt.total_seconds() / 60.0
    ).astype('float32').where(lambda s: s > 0)
    df['hour_of_day'] = df['tpep_pickup_datetime'].dt.hour.astype('Int64')
    df['day_of_week'] = df['tpep_pickup_datetime'].dt.dayofweek.astype('Int64')
    logger.success(f"Colunas inseridas com sucesso.")

    return df
