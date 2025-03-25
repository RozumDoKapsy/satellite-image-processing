from src.extractor.sentinel_hub import SentinelDataExtractor

CONFIG = {}


def main():
    sde = SentinelDataExtractor(CONFIG)
    sde.sentinelhub_authentication()
    print(sde.token)


if __name__ == '__main__':
    main()
