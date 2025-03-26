from pathlib import Path
from datetime import datetime, timedelta
import pytz

import requests
import json

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

from src.utils.log_utils import setup_loger


class SentinelDataExtractor:
    def __init__(self, cfg: dict):
        self.logger = setup_loger(self.__class__.__name__, 'extraction')

        self.secrets_path = Path(__file__).resolve().parents[2] / '.secrets'
        self.token_path = self.secrets_path / 'sentinelhub_token.json'

        self.cfg = cfg

        self.oauth = None
        self.token = None

    def get_credentials(self) -> dict:
        with open(self.secrets_path / 'credentials.json', 'r') as f:
            creds = json.load(f)
        return creds

    def save_token(self, token: dict):
        with open(self.token_path, 'w') as f:
            json.dump(token, f)

    def load_token(self):
        with open(self.token_path, 'r') as f:
            token = json.load(f)
        return token

    def expired_token_check(self) -> bool:
        token_expire_datetime = datetime.fromtimestamp(self.token['expires_at'], tz=pytz.utc)
        return token_expire_datetime <= datetime.now(pytz.utc) + timedelta(minutes=1)

    def sentinelhub_authentication(self):
        creds = self.get_credentials()
        client = BackendApplicationClient(client_id=creds['client_id'])
        self.oauth = OAuth2Session(client=client)

        self.token = self.load_token() if self.token_path.exists() else None

        if not self.token or self.expired_token_check():
            try:
                self.logger.info('Fetching new token.')
                self.token = self.oauth.fetch_token(
                    token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
                    client_secret=creds['client_secret'], include_client_id=True)

                self.save_token(self.token)
            except Exception as e:
                self.logger.error(f'Failed to fetch token: {e}')
                raise
        else:
            self.logger.info('Using existing token from file.')








