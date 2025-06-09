import datetime
import pendulum

from airflow.sdk import dag, task
from airflow.models import Variable

import json

from typing import Dict, Any, List


@dag(
    dag_id="openmeteo_extraction",
    schedule="0 0 * * *",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
    params={
        'n_days': 1
    }
)
def openmeteo_extraction():
    config_json = Variable.get('extract_config')
    CONFIG = json.loads(config_json)

    @task
    def get_dates(**context) -> Dict[str, str]:
        from datetime import datetime, timedelta
        from src.utils.common_utils import get_date_range, date_string_format

        n_days = context['params'].get('n_days', 1)

        yesterday_date = datetime.today() - timedelta(days=1)
        start_date, end_date = get_date_range(n_days, end_date=yesterday_date)
        return {
            'start_date': date_string_format(start_date),
            'end_date': date_string_format(end_date)
        }

    @task
    def extract_data(dates: Dict[str, str]) -> Dict[str, Any]:
        from src.extractors.open_meteo import OpenMeteoExtractor
        extractor = OpenMeteoExtractor(
            coords=CONFIG['location']['coordinates']
        )
        weather_data = extractor.get_history_data(
            frequency=CONFIG['weather_frequency'],
            start_date=dates['start_date'],
            end_date=dates['end_date'],
            variables=CONFIG['weather_variables']
        )
        return {
            'weather_data': weather_data,
            'lat': extractor.lat,
            'lon': extractor.lon
        }

    @task
    def transform_data(extracted_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        from src.extractors.open_meteo import OpenMeteoProcessor

        processor = OpenMeteoProcessor(CONFIG)
        processed_weather_data = processor.process(
            lat=extracted_data['lat'],
            lon=extracted_data['lon'],
            weather_data=extracted_data['weather_data']
        )
        return processed_weather_data

    @task
    def load_data(processed_weather_data):
        from src.extractors.open_meteo import OpenMeteoSaver
        from src.utils.credentials import CredentialManager

        pg_creds = CredentialManager().get_pg_credentials()
        saver = OpenMeteoSaver(pg_creds)
        saver.bulk_save(
            weather_data=processed_weather_data,
            db_name='satellite_image_processing')

    dates = get_dates()
    extracted_data = extract_data(dates)
    processed_weather_data = transform_data(extracted_data)
    load_data(processed_weather_data)


openmeteo_extraction()
