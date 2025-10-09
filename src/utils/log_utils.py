import logging
from pathlib import Path

from typing import Optional

PATH_TO_LOGS = Path(__file__).resolve().parents[2] / 'logs'


def setup_logger(file_name: Optional[str] = None) -> logging.Logger:
    """ Setups a custom logger for console handling and optional file handling.

    :param file_name: name of the file to store logs
    :return: logger
    """
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        if file_name:
            file_handler = logging.FileHandler(PATH_TO_LOGS / f'{file_name}_logs.log')
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

    return logger
