# Libraries
import logging
import os

# Modules
from logging import Logger


# Central logger configuration
def setup_logger(logger_name: str, log_file: str, level=logging.INFO) -> Logger:
    """
    Configura un logger reutilizable con un handler de archivo y consola.

    Args:
        logger_name (str): Nombre del logger.
        log_file (str): Ruta al archivo de log.
        level (int): Nivel de logging (INFO, DEBUG, etc.).
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)

    # Common format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # File handler
    file_handler = logging.FileHandler(log_file, mode="a")
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Adding handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
