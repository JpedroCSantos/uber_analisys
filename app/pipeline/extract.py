import os
import functools
import pandas as pd
from typing import Optional, List
from loguru import logger

def handle_io_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as e:
            logger.exception("ERRO DE ARQUIVO: O arquivo ou diretório não foi encontrado.", backtrace=False)
            raise FileNotFoundError("Falha na operação de I/O: arquivo não encontrado.") from e
        except pd.errors.ParserError as e:
            logger.exception("ERRO DE PARSING: Verifique a estrutura do arquivo e os parâmetros de leitura.",backtrace=False)
            raise Exception("Falha ao processar o arquivo.") from e
        except Exception as e:
            logger.exception("ERRO INESPERADO: Uma falha não prevista ocorreu durante a execução.", backtrace=False)
            raise e
    return wrapper

@handle_io_errors
def get_data_in_csv(path: str, file_name: str, delimiter: str = ";", encoding: str = "utf-8") -> pd.DataFrame:
    """
    Lê um arquivo CSV de um caminho especificado e o retorna como um DataFrame do Pandas.

    Args:
        path (str): O caminho do diretório onde o arquivo está localizado.
        file_name (str): O nome do arquivo (sem a extensão .csv).
        delimiter (str, optional): O delimitador do CSV. Defaults to ";".
        encoding (str, optional): A codificação do arquivo. Defaults to "utf-8".

    Returns:
        pd.DataFrame: Um DataFrame do Pandas contendo os dados do arquivo.
    """
    full_path = os.path.join(path, f"{file_name}.csv")
    logger.info(f"Iniciando leitura do arquivo: {full_path}")
    df = pd.read_csv(full_path, delimiter=delimiter, encoding=encoding)
    logger.success(f"Arquivo '{full_path}' lido com sucesso. Shape: {df.shape}")

    return df

@handle_io_errors
def get_data_in_parquet(path: str, file_name: str, columns: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Lê um arquivo Parquet de um caminho especificado e o retorna como um DataFrame do Pandas.

    Args:
        path (str): O caminho do diretório onde o arquivo está localizado.
        file_name (str): O nome do arquivo (sem a extensão .parquet).

    Returns:
        pd.DataFrame: Um DataFrame do Pandas contendo os dados do arquivo.
    """
    base_name = file_name[:-8] if file_name.endswith('.parquet') else file_name
    full_path = os.path.join(path, f"{base_name}.parquet")
    logger.info(f"Iniciando leitura do arquivo: {full_path}")
    df = pd.read_parquet(full_path, columns=columns)
    logger.success(f"Arquivo '{full_path}' lido com sucesso. Shape: {df.shape}")

    return df