import logging
from pathlib import Path

PATH_TO_LOGS = Path(__file__).resolve().parents[2] / 'logs'


def setup_logger(loger_name: str, file_name: str):
    logger = logging.getLogger(loger_name)
    logger.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(PATH_TO_LOGS / f'{file_name}_logs.log')
    file_handler.setLevel(logging.INFO)

    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)

    return logger
