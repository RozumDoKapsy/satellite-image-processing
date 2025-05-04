from unittest.mock import patch, MagicMock
from src.extractors.open_meteo import OpenMeteoExtractor


@patch('src.extractors.open_meteo.requests.get')
def test_get_history_data(mock_get):
    coords = {
        "min_lat": 0.0,
        "min_lon": 0.0,
        "max_lat": 1.0,
        "max_lon": 1.0
    }

    frequency = 'hourly'
    start_date = '2025-01-01'
    end_date = '2025-01-02'
    weather_variables = ['var1', 'var2']

    mock_get.return_value.content = b'{"key": "value"}'

    correct_url = ('https://api.open-meteo.com/v1/forecast?latitude=0.5&longitude=0.5'
                   '&hourly=var1,var2&start_date=2025-01-01&end_date=2025-01-02')

    logger = MagicMock()
    extractor = OpenMeteoExtractor(coords, logger)
    weather_data = extractor.get_history_data(frequency, start_date, end_date, weather_variables)

    mock_get.assert_called_once_with(correct_url)
    assert weather_data == {"key": "value"}


def test_get_mean_coords():
    coords = {
        "min_lat": 0.0,
        "min_lon": 0.0,
        "max_lat": 1.0,
        "max_lon": 1.0
    }
    logger = MagicMock()
    extractor = OpenMeteoExtractor(coords, logger)
    mean_lat, mean_lon = extractor._get_mean_coords()

    assert mean_lat == 0.5
    assert mean_lon == 0.5
