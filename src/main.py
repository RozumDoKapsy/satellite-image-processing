from src.extractor.sentinel_hub import SentinelDataExtractor

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
    'sentinel_type': 'sentinel-2-l2a'
}


def main():
    sde = SentinelDataExtractor(CONFIG)
    sde.extraction_pipeline(n_days=5)


if __name__ == '__main__':
    main()
