from src.extractors.sentinel_hub import SentinelDataPipeline
from src.extractors.open_meteo import OpenMeteoPipeline

from src.utils.log_utils import setup_logger


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


def main():
    setup_logger('extraction')
    sdp = SentinelDataPipeline(CONFIG)
    sdp.run(n_days=1)

    omp = OpenMeteoPipeline(CONFIG)
    omp.run(n_days=5)


if __name__ == '__main__':
    main()
