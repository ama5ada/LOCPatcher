import logging
import logging.handlers
import os
import sys

from config.constants import LOG_DIR, LOG_BACKUP_COUNT, MAX_LOG_BYTES

def setup_logging(log_dir: str = LOG_DIR) -> logging.Logger:
    """
    Logger instance for the patcher

    :param log_dir: Location to put logs
    :return: A logger instance
    """
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "patcher.log")

    logger = logging.getLogger("loc_patcher")

    # Avoid adding duplicate handlers if called more than once
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    logger.propagate = False

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    file_handler = logging.handlers.RotatingFileHandler(
        log_path,
        maxBytes=MAX_LOG_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(fmt)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    return logger
