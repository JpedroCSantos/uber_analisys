import os
import sys
from pathlib import Path
import hashlib
from typing import Iterable, Tuple

from loguru import logger

"""Ajuste de path para permitir execução direta do arquivo.
Garante que o diretório `app/` esteja no sys.path para resolver imports como `config.*`.
"""
CURRENT_DIR = Path(__file__).resolve().parent  # app/sql
APP_DIR = CURRENT_DIR.parent  # app
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))

from config.config import settings
from config.logging import configure_logging
from db.classes.db_class import db_class
from pipeline.extract import list_files


def compute_file_sha256(file_path: str, chunk_size: int = 1024 * 1024) -> str:
    """Calcula o hash SHA-256 de um arquivo grande de forma streaming."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as file_stream:
        while True:
            chunk = file_stream.read(chunk_size)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()


def build_file_log_rows(base_dir: str, filenames: Iterable[str], default_status: str = "pending") -> Iterable[Tuple[str, str, str]]:
    """Gera tuplas (file_name, file_hash, status) para inserção no log."""
    for filename in filenames:
        full_path = os.path.join(base_dir, filename)
        try:
            file_hash = compute_file_sha256(full_path)
        except FileNotFoundError:
            logger.error(f"Arquivo não encontrado ao calcular hash: {full_path}")
            continue
        except Exception as exc:
            logger.error(f"Falha ao calcular hash de {full_path}: {exc}")
            continue
        yield (filename, file_hash, default_status)


def upsert_file_logs(rows: Iterable[Tuple[str, str, str]]) -> int:
    """Insere/atualiza registros na tabela bronze.etl_file_log.

    Retorna a quantidade estimada de linhas processadas (baseada nas tuplas geradas).
    """
    sql = (
        "INSERT INTO bronze.etl_file_log (file_name, file_hash, status) "
        "VALUES (%s, %s, %s) "
        "ON CONFLICT (file_name) DO UPDATE SET "
        "file_hash = EXCLUDED.file_hash, "
        "processed_at = NOW(), "
        "status = EXCLUDED.status"
    )

    # Para contar, precisamos materializar as tuplas (mantendo memória sob controle)
    buffer = list(rows)
    if not buffer:
        logger.info("Nenhum arquivo encontrado para registrar no log.")
        return 0

    with db_class(config=settings.dev_db_params) as db:
        db.executemany(sql, buffer, batch_size=1000)

    return len(buffer)


def main() -> None:
    configure_logging(settings.app_env)

    base_dir = settings.data_dir
    if not os.path.isdir(base_dir):
        logger.error(f"Diretório de entrada não existe: {base_dir}")
        return

    filenames = list_files(path=base_dir)
    logger.info(f"{len(filenames)} arquivo(s) parquet encontrado(s) em {base_dir}")

    processed_count = upsert_file_logs(
        rows=build_file_log_rows(base_dir=base_dir, filenames=filenames, default_status="success")
    )

    logger.success(f"Inserção/atualização concluída. {processed_count} registro(s) processado(s) em bronze.etl_file_log.")


if __name__ == "__main__":
    main()