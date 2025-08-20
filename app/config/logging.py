import os
import sys
from loguru import logger

def configure_logging(env: str | None = None) -> None:
    env = (env or os.getenv("APP_ENV") or os.getenv("ENV") or "DEV").upper()
    log_level = os.getenv("LOG_LEVEL", "DEBUG").upper()
    os.makedirs("logs", exist_ok=True)

    logger.remove()
    logger.add(
        sys.stderr,
        level=log_level,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | {level: <8} | {message}",
    )

    logger.add(
        "logs/app.log",
        level=log_level,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
        rotation="10 MB",     
        retention="7 days",   
        enqueue=False,        
        backtrace=False,
        diagnose=False,
    )

    if env == "PROD":
        logger.add(
            "logs/app.jsonl",
            level=log_level,
            serialize=True,  # JSON por linha
            rotation="10 MB",
            retention="14 days",
            enqueue=True,
        )

def get_bound_logger(**context):
    return logger.bind(**context)
    