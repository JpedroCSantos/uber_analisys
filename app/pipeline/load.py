import os
import json
import functools
import pandas as pd

from loguru import logger
from typing import List, Literal
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

def load_csv(data_frame: pd.DataFrame, config: Settings, layer: Literal["bronze", "silver", "gold"] = "bronze") -> str:
    """
    Recebe um dataframe e transforma em um arquivo csv na camada especificada da arquitetura Medallion

    args:
        data_frame (pd.DataFrame): dataframe a ser convertido em csv
        config (Settings): configurações do sistema
        layer (str): camada da arquitetura Medallion ("bronze", "silver", "gold")

    return: "Arquivo salvo com sucesso"
    """
    from loguru import logger
    
    # Mapeia a camada para o caminho correspondente
    layer_paths = {
        "bronze": config.bronze_path,
        "silver": config.silver_path,
        "gold": config.gold_path
    }
    
    output_path = layer_paths.get(layer, config.bronze_path)
    
    logger.info(f"Salvando arquivo CSV na camada {layer.upper()} em {output_path}/{config.filename}_{layer}.csv")
    
    if not os.path.exists(output_path):
        os.makedirs(output_path)
        logger.info(f"Diretório {output_path} criado com sucesso")

    file_path = f"{output_path}/{config.filename}_{layer}.csv"
    if os.path.exists(file_path):
        os.remove(file_path)
        logger.info(f"Arquivo existente removido: {file_path}")

    data_frame.to_csv(file_path, index=False, sep=config.delimiter)
    logger.info(f"Arquivo CSV criado com sucesso na camada {layer.upper()}: {file_path}")
    
    return f"Arquivo salvo com sucesso na camada {layer.upper()}: {file_path}"

def load_bronze(data_frame: pd.DataFrame, config: Settings) -> str:
    """Wrapper para salvar na camada bronze"""
    return load_csv(data_frame, config, "bronze")

def load_silver(data_frame: pd.DataFrame, config: Settings) -> str:
    """Wrapper para salvar na camada silver"""
    return load_csv(data_frame, config, "silver")

def load_gold(data_frame: pd.DataFrame, config: Settings) -> str:
    """Wrapper para salvar na camada gold"""
    return load_csv(data_frame, config, "gold")
