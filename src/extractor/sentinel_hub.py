from pathlib import Path
from datetime import datetime, timedelta
import pytz

import requests
import json

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

from src.utils.log_utils import setup_logger
from src.db.minio_storage import save_to_minio
from src.db.pg_database import save_to_pg
from src.db.pg_data_models import SatelliteImageMetadata
from src.utils.common_utils import get_date_range, get_iso_datetime_format, get_compact_datime_format


class SentinelDataExtractor:
    def __init__(self, cfg: dict):
        self.logger = setup_logger(self.__class__.__name__, 'extraction')

        self.secrets_path = Path(__file__).resolve().parents[2] / '.secrets'
        self.token_path = self.secrets_path / 'sentinelhub_token.json'

        self.cfg = cfg
        self.bbox = self.coords2bbox()

        self.oauth = None
        self.token = None

        self.available_dates = []

    # TODO: refactor to .env
    # TODO: save credentials to .env (add them variables for creds to docker-compose)
    def get_sentinelhub_credentials(self) -> dict:
        try:
            with open(self.secrets_path / 'sentinelhub_credentials.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f'Failed to load SentinetlHub credentials: {e}')
            raise

    def get_minio_credentials(self) -> dict:
        try:
            with open(self.secrets_path / 'minio_credentials.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f'Failed to load MinIO credentials: {e}')
            raise

    def get_pg_credentials(self) -> dict:
        try:
            with open(self.secrets_path / 'pg_credentials.json', 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.error(f'Failed to load PostgreSQL credentials: {e}')
            raise

    def coords2bbox(self) -> list:
        """ Extracts coordinates from config and transforms them to bbox list.

        :return: bbox
        """
        bbox = [
            self.cfg['location']['coordinates']['min_lon'],
            self.cfg['location']['coordinates']['min_lat'],
            self.cfg['location']['coordinates']['max_lon'],
            self.cfg['location']['coordinates']['max_lat']
        ]
        return bbox

    def save_token(self, token: dict):
        with open(self.token_path, 'w') as f:
            json.dump(token, f)

    def load_token(self) -> dict:
        """ Loads existing SentinelHub API token.

        :return: token
        """
        with open(self.token_path, 'r') as f:
            token = json.load(f)
        return token

    def expired_token_check(self) -> bool:
        """ Checks whether the stored token is expired (with a 1-minute buffer).

        :return: True if token is expired
        """
        token_expire_datetime = datetime.fromtimestamp(self.token['expires_at'], tz=pytz.utc)
        return token_expire_datetime <= datetime.now(pytz.utc) + timedelta(minutes=1)

    def sentinelhub_authentication(self):
        """ Handles OAuth2 authentication with SentinelHub. Reuses a stored token if valid, otherwise requests a new one.
        """
        creds = self.get_sentinelhub_credentials()
        client = BackendApplicationClient(client_id=creds['client_id'])
        self.oauth = OAuth2Session(client=client)

        self.token = self.load_token() if self.token_path.exists() else None

        if not self.token or self.expired_token_check():
            try:
                self.logger.info('Fetching new token.')
                self.token = self.oauth.fetch_token(
                    token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
                    client_secret=creds['client_secret'], include_client_id=True)

                self.save_token(self.token)
            except Exception as e:
                self.logger.error(f'Failed to fetch token: {e}')
                raise
        else:
            self.logger.info('Using existing token from file.')

    def get_available_dates(self, iso_start_datetime: str, iso_end_datetime: str):
        """ Queries SentinelHub Catalog API for available image timestamps within a given image_datetime range and bounding box.

        :param iso_start_datetime: start datetime in ISO format
        :param iso_end_datetime: end datetime in ISO format
        """
        headers = {
            "Authorization": f"Bearer {self.token['access_token']}",
            "Content-Type": "application/json"
        }

        all_dates = []

        data = {
            "bbox": self.bbox,
            "datetime": f"{iso_start_datetime}/{iso_end_datetime}",
            "collections": [self.cfg['sentinel_type']],
            "limit": 5,
        }

        self.logger.info(f'Extracting available dates for ...')
        self.logger.info(f"Location - {self.cfg['location']['name']}")
        self.logger.info(f"Date - {iso_start_datetime} - {iso_end_datetime}")
        url = "https://sh.dataspace.copernicus.eu/api/v1/catalog/1.0.0/search"

        while True:
            try:
                response = requests.post(url, json=data, headers=headers)
                response.raise_for_status()
                response_data = response.json()

                features = response_data.get('features', [])

                if not features:
                    break

                all_dates.extend([feat['properties']['datetime'] for feat in features])

                next_page = response_data.get("context", {}).get("next")

                if next_page is None:
                    break

                data['next'] = next_page

            except requests.exceptions.RequestException as e:
                self.logger.error(f'API request failed: {e}, Response: {response.text}')
                raise

        self.available_dates = all_dates
        self.logger.info(f'Available dates: {len(self.available_dates)}')

    def get_sentinel_image(self, iso_datetime: str) -> bytes:
        """ Fetches a satellite image for a specific datetime using SentinelHub Process API.

        :param iso_datetime: target datetime in ISO format
        :return: Image data in TIFF format
        """
        headers = {
            "Authorization": f"Bearer {self.token['access_token']}",
            "Accept": "image/tiff"
        }

        evalscript = """
        //VERSION=3
        function setup() {
          return {
            input: ["B02", "B03", "B04", "B08"],
            output: { bands: 4 },
          }
        }

        function evaluatePixel(sample) {
          return [sample.B04, sample.B03, sample.B02, sample.B08]
        }
        """

        request = {
            "input": {
                "bounds": {
                    "properties": {"crs": "http://www.opengis.net/def/crs/OGC/1.3/CRS84"},
                    "bbox": self.bbox,
                },
                "data": [
                    {
                        "type": self.cfg['sentinel_type'],
                        "dataFilter": {
                            "timeRange": {
                                "from": iso_datetime,
                                "to": iso_datetime
                            }
                        },
                    }
                ],
            },
            "output": {
                "width": 512,
                "height": 512,
            },
            "evalscript": evalscript,
        }

        self.logger.info(f"Extracting {self.cfg['sentinel_type']} images for ...")
        self.logger.info(f"Location - {self.cfg['location']['name']}")
        self.logger.info(f"Date - {iso_datetime}")
        url = "https://sh.dataspace.copernicus.eu/api/v1/process"
        try:
            response = self.oauth.post(url, json=request, headers=headers).content
            return response

        except Exception as e:
            self.logger.error(f'Failed to get sentinel images: {e}')
            raise

    def save_image(self, file_name: str, image: bytes):
        """ Uploads the image to MinIO storage under the specified bucket.

        :param file_name: filename for stored image
        :param image: satellite image to save
        """
        minio_creds = self.get_minio_credentials()
        bucket_name = 'satellite-images'
        save_to_minio(minio_creds, bucket_name, file_name, image, 'image/tiff', self.logger)
        self.logger.info(f'Saved image to {bucket_name}/{file_name}')

    # TODO: mechanism to load metadata later (i.e. when PostgreSQL fails)
    def save_image_metadata(self, image_datetime, image_path: str):
        """ Saves metadata about the image (location, time, path) to PostgreSQL.

        :param image_datetime: datime of satellite image
        :param image_path: satellite image storage file path
        """
        metadata = SatelliteImageMetadata(
            satellite_type=self.cfg['sentinel_type'],
            location_name=self.cfg['location']['name'],
            image_date=image_datetime,
            min_lat=self.cfg['location']['coordinates']['min_lat'],
            min_lon=self.cfg['location']['coordinates']['min_lon'],
            max_lat=self.cfg['location']['coordinates']['max_lat'],
            max_lon=self.cfg['location']['coordinates']['max_lon'],
            image_path=image_path
        )
        creds = self.get_pg_credentials()
        save_to_pg(creds, metadata, self.logger)

    def extraction_pipeline(self, n_days: int = 1):
        """ Executes the full extraction process for the last n_days:

        Authenticates with SentinelHub
        Gets available images
        Downloads and saves each image to MinIO
        Logs metadata to PostgreSQL

        :param n_days: number of days to look back from today
        """

        self.sentinelhub_authentication()

        start_date, end_date = get_date_range(n_days)
        iso_start_date = get_iso_datetime_format(start_date)
        iso_end_date = get_iso_datetime_format(end_date)

        self.get_available_dates(iso_start_date, iso_end_date)
        for date in self.available_dates:
            try:
                image = self.get_sentinel_image(date)
                file_name = f"{get_compact_datime_format(date)}_{self.cfg['location']['name']}.tiff"
                self.save_image(file_name, image)
                self.save_image_metadata(date, file_name)
            except Exception as e:
                self.logger.error(f'Failed to process and save image for image_datetime {date}: {e}')
