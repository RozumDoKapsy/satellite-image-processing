from unittest.mock import patch, MagicMock
import datetime
from src.extractor.sentinel_hub import SentinelDataPipeline


@patch('src.extractor.sentinel_hub.CredentialManager.get_sentinelhub_credentials'
    , return_value={'client_id': 'xxx', 'client_secret': 'yyy'})
@patch('src.extractor.sentinel_hub.SentinelHubAuthenticator.authenticate')
@patch('src.extractor.sentinel_hub.CredentialManager.get_minio_credentials'
    , return_value={'endpoint': 'localhost:9000', 'access_key': 'xxx', 'secret_key': 'yyy'})
@patch('src.extractor.sentinel_hub.CredentialManager.get_pg_credentials'
    , return_value={'hostname': 'localhost', 'username': 'xxx', 'password': 'yyy'})
@patch('src.extractor.sentinel_hub.get_date_range'
    , return_value=(datetime.datetime(2025, 1, 1, 0, 0), datetime.datetime(2025, 1, 2, 0, 0)))
@patch('src.extractor.sentinel_hub.get_iso_datetime_format', return_value='2025-01-01T00:00:00.000000Z')
@patch('src.extractor.sentinel_hub.SentinelImageExtractor.get_available_dates'
    , return_value=['2025-01-01T00:00:00.000000Z', '2025-01-01T00:00:00.000000Z'])
@patch('src.extractor.sentinel_hub.SentinelImageExtractor.download_sentinel_image', return_value=b'image-bytes')
@patch('src.extractor.sentinel_hub.save_to_minio')
@patch('src.extractor.sentinel_hub.save_to_pg')
def test_data_pipeline(
        mock_save_to_pg,
        mock_save_to_minio,
        mock_download_sentinel_image,
        mock_get_available_dates,
        mock_get_iso_datetime_format,
        mock_get_date_range,
        mock_get_pg_credentials,
        mock_get_minio_credentials,
        mock_authenticate,
        mock_get_sentinelhub_credentials
):
    cfg = {
        'location': {
            'name': 'xxx',
            'coordinates': {
                'min_lon': 0.0,
                'min_lat': 0.0,
                'max_lon': 1.0,
                'max_lat': 1.0
            }
        },
        'sentinel_type': 'sentinel'
    }

    token = {"access_token": "abc", "expires_at": 9999999999}
    oauth = MagicMock()
    mock_authenticate.return_value = (token, oauth)

    pipeline = SentinelDataPipeline(cfg)
    pipeline.run(n_days=1)

    mock_get_available_dates.assert_called()
    mock_download_sentinel_image.assert_called()
    mock_save_to_minio.assert_called()
    mock_save_to_pg.assert_called()

    assert mock_download_sentinel_image.call_count == 2
