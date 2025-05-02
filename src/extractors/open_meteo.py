from pathlib import Path
import requests
import json
from datetime import datetime, timedelta
from src.utils.common_utils import get_date_range, date_string_format
from src.utils.credentials import CredentialManager
from src.db.pg_data_models import WeatherHourly
from src.db.pg_database import PostgreSaver

from typing import Tuple, Dict
import logging


class OpenMeteoExtractor:
    def __init__(self, coords: dict):
        self.coords = coords
        self.lat = self._get_mean_coords()[0]
        self.lon = self._get_mean_coords()[1]

    def _get_mean_coords(self) -> Tuple[float, float]:
        mean_lat = (self.coords['min_lat'] + self.coords['max_lat']) / 2
        mean_lon = (self.coords['min_lon'] + self.coords['max_lon']) / 2
        return mean_lat, mean_lon

    @staticmethod
    def _join_weather_variables(variables: list):
        return ','.join(variables)

    def get_history_data(self, frequency: str, start_date: str, end_date: str, variables: list) -> Dict[str, any]:
        weather_variables = self._join_weather_variables(variables)
        url = (f'https://api.open-meteo.com/v1/forecast?latitude={self.lat}&longitude={self.lon}'
               f'&{frequency}={weather_variables}&start_date={start_date}&end_date={end_date}')
        response = json.loads(requests.get(url).content)
        return response

    def get_forecast_data(self):
        pass


class OpenMeteoPipeline:
    def __init__(self, cfg: dict):
        self.logger = logging.getLogger(self.__class__.__name__)

        self.cfg = cfg
        self.secrets_path = Path(__file__).resolve().parents[2] / '.secrets'
        self.credential_manager = CredentialManager(self.secrets_path)
        self.extractor = OpenMeteoExtractor(self.cfg['location']['coordinates'])

    def run(self, history: bool = True, n_days: int = 1):
        yesterday_date = datetime.today() - timedelta(days=1)
        start_date, end_date = get_date_range(n_days, end_date=yesterday_date)
        start_date = date_string_format(start_date)
        end_date = date_string_format(end_date)

        if history:
            weather_data = self.extractor.get_history_data(
                frequency=self.cfg['weather_frequency'],
                start_date=start_date,
                end_date=end_date,
                variables=self.cfg['weather_variables']
            )

            frequency = self.cfg['weather_frequency']
            frequency_data = weather_data.get(frequency, {})

            creds = self.credential_manager.get_pg_credentials()
            postgre_saver = PostgreSaver(creds)

            records = []
            for i in range(len(weather_data[self.cfg['weather_frequency']]['time'])):
                data = WeatherHourly(
                    location_name=self.cfg['location']['name'],
                    latitude=self.extractor.lat,
                    longitude=self.extractor.lon,
                    timestamp=frequency_data['time'][i],
                    temperature_2m=(frequency_data.get('temperature_2m') or [None])[i],
                    precipitation=(frequency_data.get('precipitation') or [None])[i],
                    rain=(frequency_data.get('rain') or [None])[i],
                    soil_temperature_0cm=(frequency_data.get('soil_temperature_0cm') or [None])[i],
                    soil_moisture_0_to_1cm=(frequency_data.get('soil_moisture_0_to_1cm') or [None])[i],
                )
                postgre_saver.save('satellite_image_processing', data)
                records.append(data)
