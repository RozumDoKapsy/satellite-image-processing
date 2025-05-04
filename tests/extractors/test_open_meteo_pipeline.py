import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime

from src.extractors.open_meteo import OpenMeteoPipeline


@pytest.fixture
def config():
    cfg = {
        'location': {
            'name': 'City',
            'coordinates': {
                'min_lon': 0.0,
                'min_lat': 0.0,
                'max_lon': 1.0,
                'max_lat': 1.0
            }
        },
        'sentinel_type': 'sentinelA',
        'weather_frequency': 'daily',
        'weather_variables': ['temperature_2m', 'precipitation']
    }
    return cfg


@pytest.fixture
def weather_data():
    data = {
        'daily': {
            'time': ['2025-01-01 00:00:00', '2025-01-01 00:01:00'],
            'temperature_2m': [15.0, 18.0],
            'precipitation': [0.0, 0.5]
        },

    }
    return data


@pytest.mark.parametrize('missing_key', [
    'location',
    'weather_frequency',
    'weather_variables'
])
def test_validate_config_params(config, missing_key):
    invalid_config = config.copy()
    invalid_config.pop(missing_key)

    with pytest.raises(KeyError) as excinfo:
        OpenMeteoPipeline(invalid_config)

    assert f'Missing config key: {missing_key}' in str(excinfo.value)


@pytest.mark.parametrize('missing_key', [
    'min_lat',
    'min_lon',
    'max_lat',
    'max_lon'
])
def test_validate_config_params_coords(missing_key, config):
    invalid_config = config.copy()
    invalid_config['location']['coordinates'].pop(missing_key)

    with pytest.raises(KeyError) as excinfo:
        OpenMeteoPipeline(invalid_config)

    assert f'Missing coordinate key: {missing_key}' in str(excinfo.value)


def test_validate_config_params_correct_config(config):
    OpenMeteoPipeline(config)


@patch('src.utils.common_utils.get_date_range'
    , return_value=(datetime(2025, 1, 1, 0, 0), datetime(2025, 1, 2, 0, 0)))
@patch('src.utils.common_utils.date_string_format')
@patch('src.extractors.sentinel_hub.CredentialManager.get_pg_credentials'
    , return_value={'hostname': 'localhost', 'username': 'xxx', 'password': 'yyy'})
@patch('src.db.pg_database.PostgreSaver.save')
def test_open_meteo_pipeline(mock_pg_save, mock_get_pg_credentials,  mock_date_string_format, mock_get_date_range
                             , config, weather_data):
    mock_date_string_format.side_effect = ['2025-01-01', '2025-01-02']

    with patch('src.extractors.open_meteo.OpenMeteoExtractor.get_history_data', return_value=weather_data):
        pipeline = OpenMeteoPipeline(config)
        pipeline.run()

    mock_pg_save.assert_called()

    assert mock_pg_save.call_count == 2
