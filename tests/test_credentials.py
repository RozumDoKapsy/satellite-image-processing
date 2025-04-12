import pytest
import json
from pathlib import Path

from src.extractor.sentinel_hub import CredentialManager


def test_load_json_success(tmp_path):
    creds_file_name = 'test_credentials.json'
    creds_values = {
        'key': 'value'
    }
    creds_file_path = Path(tmp_path) / creds_file_name
    creds_file_path.write_text(json.dumps(creds_values))

    cm = CredentialManager(tmp_path)
    assert cm.load_json(creds_file_name) == creds_values


def test_load_json_error(tmp_path):
    creds_file_name = 'test_credentials.json'
    cm = CredentialManager(tmp_path)
    with pytest.raises(RuntimeError):
        cm.load_json(creds_file_name)
