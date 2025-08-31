import os
import re
import pandas as pd
import functools
from loguru import logger
from config.config import Settings


def handle_io_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception("ERRO INESPERADO: Uma falha não prevista ocorreu durante a execução.", backtrace=False)
            # raise e
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
    # logger.info(f"Colunas com valores NaN: {empty_columns}")

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
    logger.info(f"Iniciando remoção de valores NaN")
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
    df = df.copy()
    if 'store_and_fwd_flag' in df.columns:
        df.loc[:, 'store_and_fwd_flag'] = (
            df['store_and_fwd_flag']
            .map({'Y': True, 'N': False})
            .astype('boolean')
        )
    else:
        logger.debug("Coluna 'store_and_fwd_flag' ausente; ignorando mapeamento.")

    logger.success(f"Colunas tratadas com sucesso.")

    return df

@handle_io_errors
def filter_data_by_year_and_month(df: pd.DataFrame, file_name: str) -> pd.DataFrame:
    """
    Recebe um dataframe e file_name e filtra os dados por ano e mês.
    """
    year, month = get_year_and_month_from_file_name(file_name)
    if year is None or month is None:
        logger.error(f"Não foi possível extrair o ano e o mês do nome do arquivo: {file_name}")
    
    mask = (
        (df['tpep_pickup_datetime'].dt.year == year) &
        (df['tpep_pickup_datetime'].dt.month == month)
    )
    df = df.loc[mask].copy()
    logger.success(f"Filtrando dados para o ano {year} e mês {month}.")

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
    df = df.copy()
    if 'passenger_count' in df.columns:
        cleaned_passenger_count = (
            pd.to_numeric(df['passenger_count'], errors='coerce')
            .where(lambda s: s.between(1, 5))
            .astype('Int64')
        )
        df.drop(columns=['passenger_count'], inplace=True)
        df.loc[:, 'passenger_count'] = cleaned_passenger_count
    else:
        logger.debug("Coluna 'passenger_count' ausente; ignorando regra.")

    if 'trip_distance' in df.columns:
        df.loc[:, 'trip_distance'] = (
            pd.to_numeric(df['trip_distance'], errors='coerce')
            .where(lambda s: (s >= 0) & (s <= config.max_trip_distance))
            .astype('float32')
        )
    else:
        logger.debug("Coluna 'trip_distance' ausente; ignorando regra.")

    if 'duration_minutes' in df.columns:
        df.loc[:, 'duration_minutes'] = (
            pd.to_numeric(df['duration_minutes'], errors='coerce')
            .where(lambda s: (s > 0) & (s <= config.max_trip_duration))
            .astype('float32')
        )
    else:
        logger.debug("Coluna 'duration_minutes' ausente; ignorando regra.")
    
    for original_name in config.amount_columns:
        canonical = original_name.lower()
        if canonical in df.columns:
            source_name = canonical
        elif original_name in df.columns:
            source_name = original_name
        else:
            logger.debug(f"Coluna '{original_name}' ausente; criando '{canonical}' com 0.0.")
            df.loc[:, canonical] = 0.0
            df.loc[:, canonical] = df[canonical].astype('float32')
            continue

        df.loc[:, source_name] = (
            pd.to_numeric(df[source_name], errors='coerce')
            .where(lambda s: s >= 0)
            .astype('float32')
        )

        if source_name != canonical:
            df.rename(columns={source_name: canonical}, inplace=True)

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
    df = df.copy()
    df.loc[:, 'duration_minutes'] = (
        (df['tpep_dropoff_datetime'] - df['tpep_pickup_datetime'])
        .dt.total_seconds() / 60.0
    ).astype('float32').where(lambda s: s > 0)
    df.loc[:, 'hour_of_day'] = df['tpep_pickup_datetime'].dt.hour.astype('Int64')
    df.loc[:, 'day_of_week'] = df['tpep_pickup_datetime'].dt.dayofweek.astype('Int64')
    logger.success(f"Colunas inseridas com sucesso.")

    return df

def get_year_and_month_from_file_name(file_name: str) -> tuple:
    """
    Recebe um nome de arquivo e retorna o ano e o mês.
    """
    pattern = r"_(\d{4})-(\d{2})\.parquet"
    match = re.search(pattern, file_name)
    if match:
        year, month = match.groups()
        return int(year), int(month)
    else:
        return None, None