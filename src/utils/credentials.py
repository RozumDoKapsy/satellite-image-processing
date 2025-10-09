import os
from dotenv import load_dotenv
from pathlib import Path

from typing import Union, Dict, Optional


class CredentialManager:
    def __init__(self, dotenv_path: Optional[Union[str, Path]] = None):
        dotenv_path = dotenv_path or Path(__file__).resolve().parents[2] / '.env'
        if dotenv_path.exists():
            load_dotenv(dotenv_path=dotenv_path)

    @staticmethod
    def get_sentinelhub_credentials() -> Dict[str, str]:
        return {
            "client_id": os.getenv("SENTINELHUB_CLIENT_ID"),
            "client_secret": os.getenv("SENTINELHUB_CLIENT_SECRET")
        }

    @staticmethod
    def get_minio_credentials():
        return {
            "access_key": os.getenv("MINIO_ACCESS_KEY"),
            "secret_key": os.getenv("MINIO_SECRET_KEY"),
            "endpoint": os.getenv("MINIO_ENDPOINT")
        }

    @staticmethod
    def get_pg_credentials():
        return {
            "hostname": os.getenv("SATELLITE_POSTGRES_HOSTNAME"),
            "username": os.getenv("SATELLITE_POSTGRES_TECHNICAL_USER"),
            "password": os.getenv("SATELLITE_POSTGRES_TECHNICAL_PASSWORD")
        }
