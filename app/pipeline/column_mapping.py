"""
Mapeamento de colunas entre DataFrame (Pandas) e schemas SQL (Bronze/Silver)
"""
from typing import Dict
import pandas as pd
from loguru import logger

# Mapeamento de colunas originais para Bronze (snake_case)
BRONZE_COLUMN_MAPPING: Dict[str, str] = {
    'VendorID': 'vendor_id',
    'tpep_pickup_datetime': 'tpep_pickup_datetime',  # mantém o nome original
    'tpep_dropoff_datetime': 'tpep_dropoff_datetime',  # mantém o nome original
    'passenger_count': 'passenger_count',  # já está correto
    'trip_distance': 'trip_distance',  # já está correto
    'RatecodeID': 'ratecode_id',
    'store_and_fwd_flag': 'store_and_fwd_flag',  # já está correto
    'PULocationID': 'pu_location_id',
    'DOLocationID': 'do_location_id',
    'payment_type': 'payment_type',  # já está correto
    'fare_amount': 'fare_amount',  # já está correto
    'extra': 'extra',  # já está correto
    'mta_tax': 'mta_tax',  # já está correto
    'tip_amount': 'tip_amount',  # já está correto
    'tolls_amount': 'tolls_amount',  # já está correto
    'improvement_surcharge': 'improvement_surcharge',  # já está correto
    'total_amount': 'total_amount',  # já está correto
    'congestion_surcharge': 'congestion_surcharge',  # já está correto
    'Airport_fee': 'airport_fee',  # corrige maiúscula
    'cbd_congestion_fee': 'cbd_congestion_fee',  # se existir
}

# Mapeamento adicional para Silver (inclui colunas derivadas)
SILVER_COLUMN_MAPPING: Dict[str, str] = {
    **BRONZE_COLUMN_MAPPING,  # herda do Bronze
    'tpep_pickup_datetime': 'pickup_at',    # renomeia para Silver
    'tpep_dropoff_datetime': 'dropoff_at',  # renomeia para Silver
    'duration_minutes': 'duration_minutes',  # coluna derivada
    'hour_of_day': 'hour_of_day',           # coluna derivada
    'day_of_week': 'day_of_week',           # coluna derivada
}

def apply_bronze_column_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica mapeamento de colunas para a camada Bronze
    
    Args:
        df (pd.DataFrame): DataFrame com nomes originais
        
    Returns:
        pd.DataFrame: DataFrame com nomes padronizados para Bronze
    """
    logger.info("Aplicando mapeamento de colunas para Bronze...")

    if 'Airport_fee' in df.columns and 'airport_fee' in df.columns:
        logger.warning("Colunas duplicadas detectadas: 'Airport_fee' e 'airport_fee'. Consolidando para 'airport_fee'.")
        df['airport_fee'] = pd.to_numeric(df['airport_fee'], errors='coerce').fillna(
            pd.to_numeric(df['Airport_fee'], errors='coerce')
        )
        df = df.drop(columns=['Airport_fee'])

    columns_to_rename = {
        old_name: new_name 
        for old_name, new_name in BRONZE_COLUMN_MAPPING.items() 
        if old_name in df.columns and old_name != new_name
    }
    
    if columns_to_rename:
        logger.info("Renomeando colunas")
        df_renamed = df.rename(columns=columns_to_rename)
    else:
        logger.info("Nenhuma coluna precisa ser renomeada para Bronze")
        df_renamed = df.copy()

    if df_renamed.columns.duplicated().any():
        dups = [col for col, dup in zip(df_renamed.columns, df_renamed.columns.duplicated()) if dup]
        logger.warning(f"Removendo colunas duplicadas após renomeação: {dups}")
        df_renamed = df_renamed.loc[:, ~df_renamed.columns.duplicated()]
    
    # logger.success(f"Mapeamento Bronze aplicado. Colunas finais: {list(df_renamed.columns)}")
    return df_renamed

def apply_silver_column_mapping(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aplica mapeamento de colunas para a camada Silver
    
    Args:
        df (pd.DataFrame): DataFrame com nomes de Bronze ou originais
        
    Returns:
        pd.DataFrame: DataFrame com nomes padronizados para Silver
    """
    logger.info("Aplicando mapeamento de colunas para Silver...")
    
    columns_to_rename = {
        old_name: new_name 
        for old_name, new_name in SILVER_COLUMN_MAPPING.items() 
        if old_name in df.columns and old_name != new_name
    }
    
    if columns_to_rename:
        logger.info("Renomeando colunas")
        df_renamed = df.rename(columns=columns_to_rename)
    else:
        logger.info("Nenhuma coluna precisa ser renomeada para Silver")
        df_renamed = df.copy()
    
    # logger.success(f"Mapeamento Silver aplicado. Colunas finais: {list(df_renamed.columns)}")
    return df_renamed

def get_bronze_columns() -> list:
    """Retorna lista de colunas esperadas na camada Bronze"""
    return list(BRONZE_COLUMN_MAPPING.values())

def get_silver_columns() -> list:
    """Retorna lista de colunas esperadas na camada Silver"""
    return list(SILVER_COLUMN_MAPPING.values())

def validate_columns_for_bronze(df: pd.DataFrame) -> bool:
    """
    Valida se o DataFrame tem as colunas necessárias para Bronze
    
    Args:
        df (pd.DataFrame): DataFrame a ser validado
        
    Returns:
        bool: True se todas as colunas críticas estão presentes
    """
    expected_columns = get_bronze_columns()
    missing_columns = [col for col in expected_columns if col not in df.columns]
    
    if missing_columns:
        logger.warning(f"Colunas faltando para Bronze: {missing_columns}")
        return False
    
    logger.success("Todas as colunas necessárias para Bronze estão presentes")
    return True

def validate_columns_for_silver(df: pd.DataFrame) -> bool:
    """
    Valida se o DataFrame tem as colunas necessárias para Silver
    
    Args:
        df (pd.DataFrame): DataFrame a ser validado
        
    Returns:
        bool: True se todas as colunas críticas estão presentes
    """
    expected_columns = get_silver_columns()
    missing_columns = [col for col in expected_columns if col not in df.columns]
    
    if missing_columns:
        logger.warning(f"Colunas faltando para Silver: {missing_columns}")
        return False
    
    logger.success("Todas as colunas necessárias para Silver estão presentes")
    return True
