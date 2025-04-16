from src.extractors.sentinel_hub import SentinelDataPipeline

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
    'sentinel_type': 'sentinel-2-l2a'
}


def main():
    sdp = SentinelDataPipeline(CONFIG)
    sdp.run(n_days=5)


if __name__ == '__main__':
    main()
