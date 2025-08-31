import gc
import os
from loguru import logger
from config.config import settings
from db.classes.db_class import db_class
from config.logging import configure_logging
from sql.insert_input_files import compute_file_sha256
from pipeline.extract import get_data_in_parquet, get_data_in_csv, list_files
from pipeline.load import load_bronze, load_silver, load_gold
from pipeline.transform import (remove_nan_values_in_columns, get_columns_with_nan, 
                                treat_critical_columns, treat_critical_values, 
                                insert_new_columns, filter_data_by_year_and_month)
from pipeline.column_mapping import apply_bronze_column_mapping, apply_silver_column_mapping


configure_logging(settings.app_env)
if settings.export_dim_table:
    logger.info("Exportando dim table")
    df_dim_zones = get_data_in_csv( path= settings.dim_table_zones_path, 
                                    file_name=settings.table_zones_file, 
                                    delimiter=",", 
                                    dtypes=settings.dim_table_dtypes)
    rows_to_upsert = [
        (int(row.LocationID), str(row.Borough), str(row.Zone))
        for row in df_dim_zones.itertuples(index=False)
    ]
    with db_class(config=settings.dev_db_params) as db:
        db.upsert_dim_zone(rows_to_upsert)
        logger.success(f"Dim Table {settings.dim_table_name} carregada com sucesso")

files = list_files(path=settings.data_dir)
logger.info(f"{len(files)} arquivos serão processados")
with db_class(config=settings.dev_db_params) as db:
    for file in files:
        logger.info(f"Processando arquivo {file}")
        last_status = db.fetch_value(
            """
            SELECT status
            FROM bronze.etl_file_log
            WHERE file_name = %s
            """,
            (file,)
        )
        if last_status == 'success':
            logger.info(f"Arquivo {file} já processado com sucesso, pulando...")
            continue
        file_hash = compute_file_sha256(file_path=os.path.join(settings.data_dir, file))
        if last_status is None:
            logger.info(f"Arquivo {file} sem registro no log. Inserindo como pending...")
            db.execute_non_query(
                """
                INSERT INTO bronze.etl_file_log (file_name, file_hash, status)
                VALUES (%s, %s, 'pending')
                """,
                (file, file_hash)
            )
        else:
            logger.info(f"Arquivo {file} com status atual '{last_status}'. Atualizando para pending...")
            db.execute_non_query(
                """
                UPDATE bronze.etl_file_log
                SET file_hash = %s,
                    processed_at = NOW(),
                    status = 'pending'
                WHERE file_name = %s AND status <> 'success'
                """,
                (file_hash, file)
            )
        try:
            logger.info("Iniciando pipeline de dados...")
            df_bronze = get_data_in_parquet(path=settings.data_dir, file_name=file)
            logger.info("Processando dados para camada Bronze...")
            df_bronze_mapped = apply_bronze_column_mapping(df_bronze)
            # db.load_dataframe_to_table(df=df_bronze_mapped, table_name="raw_trips_landing", schema="bronze")

            logger.info("Processando dados para camada Silver...")
            df_silver = filter_data_by_year_and_month(df=df_bronze, file_name=file)
            df_silver = insert_new_columns(df=df_silver)
            df_silver = treat_critical_columns(df=df_silver)
            df_silver = treat_critical_values(df=df_silver, config=settings)
            emptyColumns = get_columns_with_nan(df=df_silver)
            df_silver = remove_nan_values_in_columns(coluns=emptyColumns, df=df_silver)
            df_silver = df_silver.sample(n=20000, random_state=42)
            df_silver_mapped = apply_silver_column_mapping(df_silver)

            db.load_dataframe_to_table(df=df_silver_mapped, table_name="fact_trips", schema="silver")
            # db.truncate_table(table_name="raw_trips_landing", schema="bronze")
            logger.success(f"Arquivo {file} processado com sucesso")
            db.execute_non_query(
                """
                UPDATE bronze.etl_file_log SET status = 'success' WHERE file_name = %s
                """,
                (file,)
            )
            del df_bronze, df_bronze_mapped, df_silver, df_silver_mapped
            gc.collect()
        except Exception as e:
            db.execute_non_query(
                """
                UPDATE bronze.etl_file_log SET status = 'failed' WHERE file_name = %s
                """,
                (file,)
            )
            logger.error(f"Erro ao processar dados: {e}")
        finally:
            logger.info("Pipeline de dados finalizado")

    db.refresh_materialized_view(view_name="agg_trips_by_hour", schema="gold")
    db.refresh_materialized_view(view_name="vendor_summary", schema="gold")
    db.refresh_materialized_view(view_name="zone_payment_summary", schema="gold")    