import os
import pandas as pd
from loguru import logger
from config.config import settings
from config.logging import configure_logging
from pipeline.extract import get_data_in_csv


def load_zones_raw() -> pd.DataFrame:
    return get_data_in_csv(
        path=settings.dim_table_zones_path,
        file_name=settings.table_zones_file,
        delimiter=",",
        dtypes=settings.dim_table_dtypes,
    )


def transform_to_dim_zone(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in ["LocationID", "Borough", "Zone"] if c in df.columns]
    df = df[cols].copy()
    df = df.rename(columns={"LocationID": "zone_id", "Borough": "borough", "Zone": "zone_name"})
    df["zone_id"] = pd.to_numeric(df["zone_id"], errors="coerce").astype("Int64")
    df["borough"] = df["borough"].astype("string")
    df["zone_name"] = df["zone_name"].astype("string")
    df = df.dropna(subset=["zone_id", "borough", "zone_name"]).drop_duplicates()
    df = df.sort_values(["zone_id"]).reset_index(drop=True)
    return df


def export_csv(df: pd.DataFrame, output_path: str = "data/input/dim_zone.csv") -> str:
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path


def main():
    configure_logging(settings.app_env)
    logger.info("Gerando CSV de dim_zone")
    raw = load_zones_raw()
    dim = transform_to_dim_zone(raw)
    out = export_csv(dim)
    logger.success(f"Arquivo gerado em {out}")


if __name__ == "__main__":
    main()


