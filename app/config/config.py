# app/pipeline/config.py
import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dotenv import load_dotenv

def load_env() -> None:
    load_dotenv(override=False)

@dataclass(frozen=True)
class Settings:
    app_env: str = field(default_factory=lambda: (os.getenv("APP_ENV") or os.getenv("ENV") or "DEV").upper())

    # Caminhos e arquivos
    data_dir: str = field(default_factory=lambda: os.getenv("DATA_DIR", "data/input"))
    input_file_base: str = field(default_factory=lambda: os.getenv("INPUT_FILE_BASE", "yellow_tripdata_2025-01"))
    input_is_parquet: bool = field(default_factory=lambda: os.getenv("INPUT_IS_PARQUET", "true").lower() == "true")

    # Leitura e performance
    use_columns: Optional[List[str]] = field(default=None) 
    chunk_size_csv: Optional[int] = field(default_factory=lambda: int(os.getenv("CHUNK_SIZE_CSV", "0")) or None)

    # Datas e dtypes
    parse_dates: List[str] = field(default_factory=lambda: ["tpep_pickup_datetime", "tpep_dropoff_datetime"])
    pandas_dtypes: Dict[str, str] = field(default_factory=lambda: {
        "VendorID": "Int64",
        "passenger_count": "Int64",
        "trip_distance": "float32",
        "RatecodeID": "Int64",
        "store_and_fwd_flag": "string",
        "PULocationID": "Int64",
        "DOLocationID": "Int64",
        "payment_type": "Int64",
        "fare_amount": "float32",
        "extra": "float32",
        "mta_tax": "float32",
        "tip_amount": "float32",
        "tolls_amount": "float32",
        "improvement_surcharge": "float32",
        "total_amount": "float32",
        "congestion_surcharge": "float32",
        "Airport_fee": "float32",
    })

    # Qualidade de dados
    critical_not_null: List[str] = field(default_factory=lambda: [
        "tpep_pickup_datetime", "tpep_dropoff_datetime", "PULocationID", "DOLocationID"
    ])
    amount_columns: List[str] = field(default_factory=lambda: [
        "fare_amount", "extra", "mta_tax", "tip_amount", "tolls_amount", "Airport_fee",
        "improvement_surcharge", "total_amount", "congestion_surcharge"
    ])

    # DB (se for usar Postgres depois)
    pg_host: str = field(default_factory=lambda: os.getenv("PG_HOST", "localhost"))
    pg_port: int = field(default_factory=lambda: int(os.getenv("PG_PORT", "5432")))
    pg_user: str = field(default_factory=lambda: os.getenv("PG_USER", "postgres"))
    pg_password: str = field(default_factory=lambda: os.getenv("PG_PASSWORD", "postgres"))
    pg_database: str = field(default_factory=lambda: os.getenv("PG_DATABASE", "uber"))

load_env()
settings = Settings()