import os
import sys
from loguru import logger

def configure_logging(env: str | None = None) -> None:
    env = (env or os.getenv("APP_ENV") or os.getenv("ENV") or "DEV").upper()
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    os.makedirs("logs", exist_ok=True)

    logger.remove()

    if env == "DEV":
        logger.add(
            sys.stderr,
            level="DEBUG",
            backtrace=True,
            diagnose=True,
            colorize=True,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | {level: <8} | {name}:{function}:{line} - {message}",
        )
    else:
        logger.add(
            sys.stderr,
            level=log_level,
            backtrace=False,
            diagnose=False,
            format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level} | {message}",
        )
        logger.add(
            "logs/app.jsonl",
            level=log_level,
            rotation="10 MB",
            retention="14 days",
            enqueue=True,
            serialize=True,  # JSON por linha
        )

def get_bound_logger(**context):
    return logger.bind(**context)