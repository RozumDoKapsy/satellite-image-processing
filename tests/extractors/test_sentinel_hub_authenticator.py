from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import pytz
from src.extractors.sentinel_hub import SentinelHubAuthenticator


@patch('src.extractors.sentinel_hub.OAuth2Session.fetch_token')
def test_fetch_token(mock_fetch_token, tmp_path):
    credentials = {"client_id": "client", "client_secret": "secret"}
    token_path = tmp_path / "token.json"
    logger = MagicMock()

    mock_fetch_token.return_value = {"access_token": "abc", "expires_at": 9999999999}

    auth = SentinelHubAuthenticator(credentials, token_path, logger)
    token, oauth = auth.authenticate()

    assert token['access_token'] == 'abc'


def test_expired_token_check(tmp_path):
    credentials = {"client_id": "client", "client_secret": "secret"}
    token_path = tmp_path / "token.json"
    logger = MagicMock()

    auth = SentinelHubAuthenticator(credentials, token_path, logger)
    auth.token = {"expires_at": (datetime.now(pytz.utc) - timedelta(minutes=10)).timestamp()}
    assert auth.expired_token_check() is True
