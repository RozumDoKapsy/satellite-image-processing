from pathlib import Path

from src.extractor.sentinel_hub import SentinelDataExtractor

BASE_PATH = Path(__file__).resolve().parents[1]
PATH_TO_DATA = BASE_PATH / 'data'
PATH_TO_IMAGES = PATH_TO_DATA / 'images'

CONFIG = {
    'location': {
        'name': 'Cerhenice',
        'coordinates': [
            15.0492,
            50.0566,
            15.0949,
            50.0859
        ]
    },
    'sentinel_type': 'sentinel-2-l2a',
    'path_to_images': PATH_TO_IMAGES
}


def main():
    sde = SentinelDataExtractor(CONFIG)
    sde.extraction_pipeline(n_days=5)


if __name__ == '__main__':
    main()
