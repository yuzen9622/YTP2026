"""Loguru logging setup — dev/prod split file output."""
import os
import sys
from pathlib import Path

from loguru import logger

from app.core.config import settings


def setup_logging() -> None:
    """Configure loguru logger for the current app_env.

    Console: always writes to stderr (colorized in dev, plain in prod).
    Files: written under logs/{app_env}/.
      - app.log: all DEBUG+ messages
      - error.log (prod only): ERROR+ messages only

    On Windows with multi-worker mode, all workers share the same files.
    To avoid WinError 32 file-lock conflicts during rename, rotation/compression
    are disabled on Windows and only enabled on non-Windows platforms.
    """
    log_dir = Path(settings.log_dir_base) / settings.app_env
    log_dir.mkdir(parents=True, exist_ok=True)

    is_windows = os.name == "nt"
    app_log_file = log_dir / "app.log"
    error_log_file = log_dir / "error.log"
    common_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | "
        "{name}:{function}:{line} — {message}"
    )

    logger.remove()  # Remove the default stderr handler added at import time.

    # Console output
    console_level = "DEBUG" if settings.app_env == "development" else "INFO"
    logger.add(
        sys.stderr,
        level=console_level,
        colorize=settings.app_env == "development",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> — "
            "<level>{message}</level>"
        ),
    )

    # Main application log file — shared by all workers.
    app_sink_kwargs = {
        "level": "DEBUG",
        "enqueue": True,
        "delay": is_windows,
        "format": common_format,
    }
    if not is_windows:
        app_sink_kwargs.update(
            {
                "rotation": "00:00",
                "retention": "14 days",
                "compression": "zip",
            }
        )
    logger.add(app_log_file, **app_sink_kwargs)

    # Production error log — ERROR+ only.
    if settings.app_env == "production":
        error_sink_kwargs = {
            "level": "ERROR",
            "enqueue": True,
            "delay": is_windows,
            "format": common_format,
        }
        if not is_windows:
            error_sink_kwargs.update(
                {
                    "rotation": "00:00",
                    "retention": "30 days",
                    "compression": "zip",
                }
            )
        logger.add(error_log_file, **error_sink_kwargs)
