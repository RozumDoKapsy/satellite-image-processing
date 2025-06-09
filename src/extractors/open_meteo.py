import requests
from datetime import datetime, timedelta
from src.utils.common_utils import get_date_range, date_string_format
from src.utils.credentials import CredentialManager
from src.db.pg_data_models import WeatherHourly
from src.db.pg_database import PostgreSaver

from typing import Tuple, Dict, List, Any, Union
import logging


class OpenMeteoExtractor:
    """ Extracts historical or forecast weather data from the Open-Meteo API.
    :param coords: dictionary containing coordinate bounds (bbox) with keys 'min_lat', 'max_lat', 'min_lon', 'max_lon'
    """
    def __init__(self, coords: Dict):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.coords = coords
        self.lat = self._get_mean_coords()[0]
        self.lon = self._get_mean_coords()[1]

    def _get_mean_coords(self) -> Tuple[float, float]:
        """ Calculate the average latitude and longitude from the provided coordinates.
        :return: latitude, longitude
        """
        mean_lat = (self.coords['min_lat'] + self.coords['max_lat']) / 2
        mean_lon = (self.coords['min_lon'] + self.coords['max_lon']) / 2
        return mean_lat, mean_lon

    @staticmethod
    def _join_weather_variables(variables: List[str]) -> str:
        """ Join weather variable names into a comma-separated string. Used as API call parameter.

        :param variables: list of weather variables
        :return: comma-separated weather variables
        """
        return ','.join(variables)

    def get_history_data(self, frequency: str, start_date: str, end_date: str, variables: list) -> Dict[str, Any]:
        """ Fetch historical weather data from OpenMeteo API.

        :param frequency: data frequency (e.g. daily, hourly)
        :param start_date: start date in ISO format (YYYY-MM-DD)
        :param end_date: end date in ISO format (YYYY-MM-DD)
        :param variables: list of weather variables to extract
        :return: weather data as a JSON-compatible dictionary
        :raises: requests.exceptions.RequestException if API call fails
        """

        weather_variables = self._join_weather_variables(variables)
        url = (f'https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}'
               f'&{frequency}={weather_variables}&start_date={start_date}&end_date={end_date}')

        self.logger.info(
            f'Extracting weather data | url={url}\n'
            f'lat={self.lat} lon={self.lon}\n'
            f'from={start_date} to={end_date}\n'
            f'variables={variables} frequency={frequency}'
        )
        try:
            response = requests.get(url)
            self.logger.debug(f'API status code: {response.status_code}')
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.logger.error(f'API request failed: {e}')
            raise

    def get_forecast_data(self):
        pass


class OpenMeteoProcessor:
    """ Processes raw weather data fetched from the Open-Meteo API.

    :param cfg: configuration dictionary
    """
    def __init__(self, cfg: Dict):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cfg = cfg

    @staticmethod
    def _safe_get(lst: List[Any], idx: int) -> Union[Any, None]:
        """ Safely retrieve an element from a list by index.
        The main purpose is to avoid IndexError.

        :param lst: list of items
        :param idx: index to retrieve
        :return: element at the index or None if out of bounds
        """
        return lst[idx] if lst and idx < len(lst) else None

    def process(self, weather_data: Dict[str, Any], lat: float, lon: float) -> List[Dict[str, Any]]:
        """ Transforms the raw weather API response into a list of structured records for further processing
        or database insertion.

        :param weather_data: raw weather data dictionary
        :param lat: latitude
        :param lon: longitude
        :return: list of structured records
        :raise KeyError: if specified frequency (in config) not in raw data
        :raise KeyError: if 'time' not in raw data
        """
        if self.cfg['weather_frequency'] not in weather_data:
            raise KeyError(f"Key '{self.cfg['weather_frequency']}' not present in Weather Data.")

        frequency = self.cfg['weather_frequency']
        frequency_data = weather_data.get(frequency, {})

        if 'time' not in frequency_data:
            raise KeyError(f"Key 'time' not present in Weather Data.")

        result = []
        for i in range(len(weather_data[self.cfg['weather_frequency']]['time'])):
            data = {
                'location_name': self.cfg['location']['name'],
                'latitude': lat,
                'longitude': lon,
                'timestamp': frequency_data['time'][i],
                'temperature_2m': self._safe_get(frequency_data.get('temperature_2m'), i),
                'precipitation': self._safe_get(frequency_data.get('precipitation'), i),
                'rain': self._safe_get(frequency_data.get('rain'), i),
                'soil_temperature_0cm': self._safe_get(frequency_data.get('soil_temperature_0cm'), i),
                'soil_moisture_0_to_1cm': self._safe_get(frequency_data.get('soil_moisture_0_to_1cm'), i)
            }
            result.append(data)
        return result


class OpenMeteoSaver:
    """ Saves processed weather data to a PostgreSQL database.

    :param creds: dictionary of database credentials
    """
    def __init__(self, creds: Dict):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.postgre_saver = PostgreSaver(creds)

    @staticmethod
    def _weather_hourly_object(data: Dict[str, Any]) -> WeatherHourly:
        """ Convert dictionary data into a WeatherHourly SQL Alchemy ORM object.

        :param data: dictionary representning one weather record
        :return: WeatherHourly ORM object
        """
        # TODO: tightly coupled with table WeatherHourly
        return WeatherHourly(
                location_name=data['location_name'],
                latitude=data['latitude'],
                longitude=data['longitude'],
                timestamp=data['timestamp'],
                temperature_2m=data['temperature_2m'],
                precipitation=data['precipitation'],
                rain=data['rain'],
                soil_temperature_0cm=data['soil_temperature_0cm'],
                soil_moisture_0_to_1cm=data['soil_moisture_0_to_1cm'],
            )

    def bulk_save(self, weather_data: List[Dict[str, Any]], db_name: str):
        """ Save a batch of weather data records into the database.

        :param weather_data: list of weather data dictionaries
        :param db_name: database name to which we want to store data
        """
        # TODO: tightly coupled with table WeatherHourly
        for data in weather_data:
            self.postgre_saver.save(db_name, self._weather_hourly_object(data))

        if self.postgre_saver.skipped_rows > 0:
            self.logger.warning(f'Skipped {self.postgre_saver.skipped_rows} rows.')


class OpenMeteoPipeline:
    """

    """
    def __init__(self, cfg: Dict):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.cfg = cfg
        self._validate_config_params()
        self.credential_manager = CredentialManager()
        self.extractor = OpenMeteoExtractor(self.cfg['location']['coordinates'])
        self.processor = OpenMeteoProcessor(self.cfg)
        self.saver = OpenMeteoSaver(self.credential_manager.get_pg_credentials())

    def _validate_config_params(self):
        """ Checks if required keys are present in config dictionary.

        :raise KeyError: if any required key is missing in configuration
        """
        required_keys = ['location', 'weather_frequency', 'weather_variables']
        for key in required_keys:
            if key not in self.cfg:
                raise KeyError(f'Missing config key: {key}')

        coord_keys = ['min_lat', 'max_lat', 'min_lon', 'max_lon']
        for key in coord_keys:
            if key not in self.cfg['location'].get('coordinates', {}):
                raise KeyError(f'Missing coordinate key: {key}')

    def run(self, history: bool = True, n_days: int = 1) -> None:
        """ Execute the ETL pipeline for weather data.

        :param history: weather to extract historical data or forecast data (if False)
        :param n_days: number of days to fetch data
        """
        yesterday_date = datetime.today() - timedelta(days=1)
        start_date, end_date = get_date_range(n_days, end_date=yesterday_date)
        start_date = date_string_format(start_date)
        end_date = date_string_format(end_date)

        if history:
            try:
                weather_data = self.extractor.get_history_data(
                    frequency=self.cfg['weather_frequency'],
                    start_date=start_date,
                    end_date=end_date,
                    variables=self.cfg['weather_variables']
                )

                processed_weather_data = self.processor.process(
                    weather_data=weather_data,
                    lat=self.extractor.lat,
                    lon=self.extractor.lon)

                self.saver.bulk_save(
                    weather_data=processed_weather_data,
                    db_name='satellite_image_processing')

            except Exception as e:
                self.logger.error(f'Failed to process and save weather data: {e}')
