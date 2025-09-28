import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dotenv import load_dotenv


def load_env() -> None:
    load_dotenv(override=False)

load_env()

@dataclass(frozen=False)
class Settings:
    def __post_init__(self):
        """
        Define o data_dir com base no ambiente, mas APENAS se ele
        não foi definido explicitamente pela variável de ambiente DIR.
        """
        if self.data_dir is not None:
            return
        
        if self.etl_mode == "DEMO":
            self.data_dir = "data/input/demo_mode"
        else:
            self.data_dir = "data/input/yellow_trip"

    data_dir: str = field(default_factory=lambda: os.getenv("DATA_DIR"))
    export_to_db: bool = field(default_factory=lambda: os.getenv("EXPORT_TO_DB", "false").lower() == "true")
    app_env: str = field(default_factory=lambda: (os.getenv("APP_ENV") or os.getenv("ENV") or "DEV").upper())
    etl_mode: str = field(default_factory=lambda: os.getenv("ETL_MODE", "FULL"))

    # Leitura e performance
    use_columns: Optional[List[str]] = field(default=None) 
    chunk_size_csv: Optional[int] = field(default_factory=lambda: int(os.getenv("CHUNK_SIZE_CSV", "0")) or None)

    # Amostragem
    sample_enabled: bool = field(default_factory=lambda: os.getenv("SAMPLE_ENABLED", "true").lower() == "true")
    sample_n: int = field(default_factory=lambda: int(os.getenv("SAMPLE_N", "20000")))
    sample_random_state: int = field(default_factory=lambda: int(os.getenv("SAMPLE_RANDOM_STATE", "42")))

    # Datas e dtypes
    parse_dates: List[str] = field(default_factory=lambda: ["tpep_pickup_datetime", "tpep_dropoff_datetime"])
    dim_table_zones_path: str = field(default_factory=lambda: os.getenv("DIM_TABLE_ZONES_PATH", "data/input/taxi_zones"))
    table_zones_file: str = field(default_factory=lambda: os.getenv("ZONES_FILE", "taxi_zone_lookup"))
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

    # Dim Table
    dim_table_name: str = field(default_factory=lambda: os.getenv("DIM_TABLE_NAME", "dim_zone"))
    export_dim_table: bool =  field(default_factory=lambda: os.getenv("EXPORT_DIM_TABLE", "true").lower() == "true")
    dim_table_dtypes: Dict[str, str] = field(default_factory=lambda: {
        'LocationID': 'Int64',
        'Borough': 'string',
        'Zone': 'string',
        'service_zone': 'string'
    })

    # Qualidade de dados
    critical_not_null: List[str] = field(default_factory=lambda: [
        "tpep_pickup_datetime", "tpep_dropoff_datetime", "PULocationID", "DOLocationID"
    ])
    amount_columns: List[str] = field(default_factory=lambda: [
        "fare_amount", "extra", "mta_tax", "tip_amount", "tolls_amount", "Airport_fee",
        "improvement_surcharge", "total_amount", "congestion_surcharge"
    ])
    max_trip_distance: float = field(default_factory=lambda: float(os.getenv("MAX_TRIP_DISTANCE", "300")))
    max_trip_duration: float = field(default_factory=lambda: float(os.getenv("MAX_TRIP_DURATION", "480")))

    dev_db_params: Dict[str, any] = field(default_factory=lambda: {
        "host": os.getenv("PG_HOST", "localhost"),
        "port": int(os.getenv("PG_PORT", "5432")),
        "dbname": os.getenv("PG_DATABASE", "trips_analysis"),
        "user": os.getenv("PG_USER", "etl_process"),
        "password": os.getenv("PG_PASSWORD", "postgres")
    })
    
    # Arquitetura Medallion - Caminhos de saída
    output_path: str = field(default_factory=lambda: os.getenv("OUTPUT_PATH", "data/output"))
    bronze_path: str = field(default_factory=lambda: os.getenv("BRONZE_PATH", "data/output/bronze"))
    silver_path: str = field(default_factory=lambda: os.getenv("SILVER_PATH", "data/output/silver"))
    gold_path: str = field(default_factory=lambda: os.getenv("GOLD_PATH", "data/output/gold"))
    output_name: str = field(default_factory=lambda: os.getenv("OUTPUT_NAME", "gold_trips"))
    output_format: str = field(default_factory=lambda: (os.getenv("OUTPUT_FORMAT", "csv").lower()))
    
    # Configurações de arquivo
    filename: str = field(default_factory=lambda: os.getenv("FILENAME", "trips_data"))
    delimiter: str = field(default_factory=lambda: os.getenv("DELIMITER", ","))
    
    # Configurações de qualidade por camada
    bronze_quality: Dict[str, any] = field(default_factory=lambda: {
        "validation_level": "basic",
        "required_columns": ["tpep_pickup_datetime", "tpep_dropoff_datetime"],
        "allow_duplicates": True
    })
    
    silver_quality: Dict[str, any] = field(default_factory=lambda: {
        "validation_level": "intermediate",
        "required_columns": ["tpep_pickup_datetime", "tpep_dropoff_datetime", "PULocationID", "DOLocationID"],
        "allow_duplicates": False,
        "null_threshold": 0.1
    })
    
    gold_quality: Dict[str, any] = field(default_factory=lambda: {
        "validation_level": "strict",
        "required_columns": ["tpep_pickup_datetime", "tpep_dropoff_datetime", "PULocationID", "DOLocationID", "total_amount"],
        "allow_duplicates": False,
        "null_threshold": 0.0,
        "business_rules": ["positive_amounts", "valid_coordinates"]
    })

    # Database config
    pg_sslmode: str = field(default_factory=lambda: os.getenv("PG_SSLMODE", "prefer"))
    

settings = Settings()