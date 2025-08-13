from loguru import logger
from config.config import settings
from config.logging import configure_logging
from pipeline.extract import get_data_in_parquet
from pipeline.transform import (remove_nan_values_in_columns, get_columns_with_nan, 
                                treat_critical_columns, treat_critical_values, 
                                insert_new_columns)
from pipeline.load import load_bronze, load_silver, load_gold

configure_logging(settings.app_env)

logger.info("Iniciando pipeline de dados...")
df = get_data_in_parquet(path=settings.data_dir, file_name=settings.input_file_base)

logger.info("Processando dados para camada Bronze...")
df = insert_new_columns(df=df)
df = treat_critical_columns(df=df)
df = treat_critical_values(df=df, config=settings)
emptyColumns = get_columns_with_nan(df=df)
df = remove_nan_values_in_columns(coluns=emptyColumns, df=df)

logger.info(f"Shape: {df.shape}")



# from loguru import logger
# from config.config import settings
# from config.logging import configure_logging
# from pipeline.extract import get_data_in_parquet
# from pipeline.transform import (remove_nan_values_in_columns, get_columns_with_nan, 
#                                 treat_critical_columns, treat_critical_values, 
#                                 insert_new_columns)
# from pipeline.load import load_bronze, load_silver, load_gold

# configure_logging(settings.app_env)

# # Extração dos dados
# logger.info("Iniciando pipeline de dados...")
# df = get_data_in_parquet(path=settings.data_dir, file_name=settings.input_file_base)

# # Transformações básicas para camada Bronze
# logger.info("Processando dados para camada Bronze...")
# df_bronze = insert_new_columns(df=df.copy())
# load_bronze(df_bronze, settings)

# # Transformações intermediárias para camada Silver
# logger.info("Processando dados para camada Silver...")
# df_silver = treat_critical_columns(df=df_bronze.copy())
# df_silver = treat_critical_values(df=df_silver, config=settings)
# load_silver(df_silver, settings)

# # Transformações avançadas para camada Gold
# logger.info("Processando dados para camada Gold...")
# df_gold = df_silver.copy()
# emptyColumns = get_columns_with_nan(df=df_gold)
# df_gold = remove_nan_values_in_columns(coluns=emptyColumns, df=df_gold)
# load_gold(df_gold, settings)

# logger.info(f"Pipeline concluído! Shape final: {df_gold.shape}")
# logger.info("Arquivos salvos nas camadas Bronze, Silver e Gold com sucesso!")