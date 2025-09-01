import gc
import os
import pandas as pd
from loguru import logger
from config.config import settings
from db.classes.db_class import db_class
from config.logging import configure_logging
from sql.insert_input_files import compute_file_sha256
from pipeline.extract import get_data_in_parquet, get_data_in_csv, list_files
from pipeline.transform import (
    remove_nan_values_in_columns,
    get_columns_with_nan,
    treat_critical_columns,
    treat_critical_values,
    insert_new_columns,
    filter_data_by_year_and_month,
)
from pipeline.column_mapping import (
    apply_bronze_column_mapping,
    apply_silver_column_mapping,
    align_silver_output_columns,
    align_silver_output_file_columns,
)


def list_input_files() -> list[str]:
    return list_files(path=settings.data_dir)


def read_bronze_file(file_name: str):
    return get_data_in_parquet(path=settings.data_dir, file_name=file_name)


def build_silver_dataframe(df_bronze, file_name: str):
    df_silver = filter_data_by_year_and_month(df=df_bronze, file_name=file_name)
    df_silver = insert_new_columns(df=df_silver)
    df_silver = treat_critical_columns(df=df_silver)
    df_silver = treat_critical_values(df=df_silver, config=settings)
    empty_columns = get_columns_with_nan(df=df_silver)
    df_silver = remove_nan_values_in_columns(coluns=empty_columns, df=df_silver)
    if settings.sample_enabled:
        df_silver = df_silver.sample(n=settings.sample_n, random_state=settings.sample_random_state)
    return apply_silver_column_mapping(df_silver)


def _compute_output_path() -> str:
    os.makedirs(settings.gold_path, exist_ok=True)
    base_name, _ = os.path.splitext(settings.output_name)
    ext = 'parquet' if settings.output_format == 'parquet' else 'csv'
    return os.path.join(settings.gold_path, f"{base_name}.{ext}")


def save_gold(df):
    df = align_silver_output_file_columns(df)
    out_path = _compute_output_path()
    if settings.output_format == 'parquet':
        if os.path.exists(out_path):
            existing = pd.read_parquet(out_path)
            existing = align_silver_output_file_columns(existing)
            df = pd.concat([existing, df], ignore_index=True)
        df.to_parquet(out_path, index=False)
    else:
        write_header = not os.path.exists(out_path)
        df.to_csv(
            out_path,
            index=False,
            mode=('w' if write_header else 'a'),
            header=write_header,
            sep=';',
            decimal=',',
        )
    return out_path


def upsert_dim_zones(db):
    if not settings.export_dim_table:
        return
    df_dim_zones = get_data_in_csv(
        path=settings.dim_table_zones_path,
        file_name=settings.table_zones_file,
        delimiter=",",
        dtypes=settings.dim_table_dtypes,
    )
    rows_to_upsert = [
        (int(row.LocationID), str(row.Borough), str(row.Zone))
        for row in df_dim_zones.itertuples(index=False)
    ]
    db.upsert_dim_zone(rows_to_upsert)


def process_file_without_db(file_name: str):
    logger.info(f"Processando arquivo {file_name}")
    df_bronze = read_bronze_file(file_name)
    df_silver_mapped = build_silver_dataframe(df_bronze, file_name)
    out_path = save_gold(df_silver_mapped)
    del df_bronze, df_silver_mapped
    gc.collect()
    logger.success(f"Arquivo gerado em {out_path}")


def process_file_with_db(db, file_name: str):
    logger.info(f"Processando arquivo {file_name}")
    last_status = db.fetch_value(
        """
        SELECT status
        FROM bronze.etl_file_log
        WHERE file_name = %s
        """,
        (file_name,),
    )
    if last_status == "success":
        logger.info(f"Arquivo {file_name} já processado com sucesso, pulando...")
        return
    file_hash = compute_file_sha256(file_path=os.path.join(settings.data_dir, file_name))
    if last_status is None:
        db.execute_non_query(
            """
            INSERT INTO bronze.etl_file_log (file_name, file_hash, status)
            VALUES (%s, %s, 'pending')
            """,
            (file_name, file_hash),
        )
    else:
        db.execute_non_query(
            """
            UPDATE bronze.etl_file_log
            SET file_hash = %s,
                processed_at = NOW(),
                status = 'pending'
            WHERE file_name = %s AND status <> 'success'
            """,
            (file_hash, file_name),
        )
    try:
        df_bronze = read_bronze_file(file_name)
        df_bronze_mapped = apply_bronze_column_mapping(df_bronze)
        db.load_dataframe_to_table(df=df_bronze_mapped, table_name="raw_trips_landing", schema="bronze")
        df_silver_mapped = build_silver_dataframe(df_bronze, file_name)
        df_silver_mapped = align_silver_output_columns(df_silver_mapped)
        db.load_dataframe_to_table(df=df_silver_mapped, table_name="fact_trips", schema="silver")
        db.truncate_table(table_name="raw_trips_landing", schema="bronze")
        db.execute_non_query(
            """
            UPDATE bronze.etl_file_log SET status = 'success' WHERE file_name = %s
            """,
            (file_name,),
        )
        del df_bronze, df_bronze_mapped, df_silver_mapped
        gc.collect()
        logger.success(f"Arquivo {file_name} processado com sucesso")
    except Exception as e:
        db.execute_non_query(
            """
            UPDATE bronze.etl_file_log SET status = 'failed' WHERE file_name = %s
            """,
            (file_name,),
        )
        logger.error(f"Erro ao processar dados: {e}")
    finally:
        logger.info("Pipeline de dados finalizado")


 


def run_pipeline_without_db():
    files = list_input_files()
    logger.info(f"{len(files)} arquivos serão processados")
    for file in files:
        process_file_without_db(file)


def run_pipeline_with_db():
    files = list_input_files()
    logger.info(f"{len(files)} arquivos serão processados")
    with db_class(config=settings.dev_db_params) as db:
        upsert_dim_zones(db)
        for file in files:
            process_file_with_db(db, file)
        db.refresh_materialized_view(view_name="agg_trips_by_hour", schema="gold")
        db.refresh_materialized_view(view_name="vendor_summary", schema="gold")
        db.refresh_materialized_view(view_name="zone_payment_summary", schema="gold")


def main():
    configure_logging(settings.app_env)
    if settings.export_to_db:
        run_pipeline_with_db()
    else:
        run_pipeline_without_db()


if __name__ == "__main__":
    main()