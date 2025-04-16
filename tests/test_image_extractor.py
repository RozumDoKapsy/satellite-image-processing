from unittest.mock import patch, MagicMock

from src.extractors.sentinel_hub import SentinelImageExtractor


@patch('src.extractors.sentinel_hub.requests.post')
def test_get_available_dates(mock_post):
    iso_datetime = '2024-01-01T00:00:00Z'
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "features": [{"properties": {"datetime": iso_datetime}}],
        "context": {"next": None}
    }

    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response

    cfg = {
        "location": {
            "name": "test",
            "coordinates": {
                "min_lat": 0.0,
                "min_lon": 0.0,
                "max_lat": 1.0,
                "max_lon": 1.0
            }
        },
       "sentinel_type": "sentinel-2"
    }
    oauth = MagicMock()
    token = {"access_token": "abc"}
    logger = MagicMock()

    extractor = SentinelImageExtractor(cfg, oauth, token, logger)
    dates = extractor.get_available_dates(iso_datetime, iso_datetime)

    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args

    assert dates == [iso_datetime]
    assert args[0] == 'https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search'
    assert kwargs['headers']['Authorization'] == 'Bearer abc'
    assert kwargs['json']['bbox'] == [0.0, 0.0, 1.0, 1.0]


def test_download_image():
    cfg = {
        "location": {
            "name": "test",
            "coordinates": {
                "min_lat": 0.0,
                "min_lon": 0.0,
                "max_lat": 1.0,
                "max_lon": 1.0
            }
        },
       "sentinel_type": "sentinel-2"
    }
    oauth = MagicMock()
    token = {"access_token": "abc"}
    logger = MagicMock()

    oauth.post.return_value.content = b'image-bytes'

    iso_datetime = '2024-01-01T00:00:00Z'
    extractor = SentinelImageExtractor(cfg, oauth, token, logger)
    response = extractor.download_sentinel_image(iso_datetime)

    oauth.post.assert_called_once()
    args, kwargs = oauth.post.call_args

    assert response == b'image-bytes'
    assert args[0] == 'https://sh.dataspace.copernicus.eu/api/v1/process'
    assert kwargs['headers']['Authorization'] == 'Bearer abc'
    assert kwargs['headers']['Accept'] == 'image/tiff'
    assert kwargs['json']['input']['bounds']['bbox'] == [0.0, 0.0, 1.0, 1.0]
