from loguru import logger
from config.config import settings
from config.logging import configure_logging
from pipeline.extract import getDataInParquet
from pipeline.transform import (remove_nan_values_in_columns, get_columns_with_nan, 
                                treat_critical_columns, treat_critical_values, 
                                insert_new_columns)

configure_logging(settings.app_env)
df = getDataInParquet(path=settings.data_dir, file_name=settings.input_file_base)

df = insert_new_columns(df=df)
df = treat_critical_columns(df=df)
df = treat_critical_values(df=df, config=settings)
emptyColumns = get_columns_with_nan(df=df)
df = remove_nan_values_in_columns(coluns=emptyColumns, df=df)

logger.info(f"Shape: {df.shape}")



