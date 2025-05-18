import datetime
import pendulum

from airflow.sdk import dag, task
from src.extractors.open_meteo import OpenMeteoPipeline

CONFIG = {
    'location': {
        'name': 'Cerhenice',
        'coordinates': {
            'min_lon': 15.0492,
            'min_lat': 50.0566,
            'max_lon': 15.0949,
            'max_lat': 50.0859
        }
    },
    'sentinel_type': 'sentinel-2-l2a',
    'weather_frequency': 'hourly',
    'weather_variables': [
        'temperature_2m',
        'precipitation',
        'rain',
        'soil_temperature_0cm',
        'soil_moisture_0_to_1cm'
    ]
}


@dag(
    dag_id="extract_openmeteo",
    schedule="0 0 * * *",
    start_date=pendulum.datetime(2021, 1, 1, tz="UTC"),
    catchup=False,
    dagrun_timeout=datetime.timedelta(minutes=60),
)
def ExtractOpenMeteo():
    @task
    def extract():
        omp = OpenMeteoPipeline(CONFIG)
        omp.run(n_days=5)
    extract()


ExtractOpenMeteo()
