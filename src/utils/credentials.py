from pathlib import Path
import json

from typing import Union


class CredentialManager:
    # TODO: refactor to .env
    # TODO: save credentials to .env (add them variables for creds to docker-compose)
    def __init__(self, secrets_path: Union[str, Path]):
        self.secrets_path = Path(secrets_path)

    def load_json(self, filename: str):
        try:
            with open(self.secrets_path / filename, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            raise RuntimeError(f'Failed to load {filename}: {e}')

    def get_sentinelhub_credentials(self):
        return self.load_json('sentinelhub_credentials.json')

    def get_minio_credentials(self):
        return self.load_json('minio_credentials.json')

    def get_pg_credentials(self):
        return self.load_json('pg_credentials.json')

    def get_open_meteo_credentials(self):
        return self.load_json('open_meteo_credentials.json')
