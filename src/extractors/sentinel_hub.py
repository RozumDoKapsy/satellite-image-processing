from pathlib import Path
from datetime import datetime, timedelta
import pytz

import requests
import json

from oauthlib.oauth2 import BackendApplicationClient
from requests_oauthlib import OAuth2Session

from src.db.minio_storage import MinIOSaver
from src.db.pg_database import PostgreSaver
from src.db.pg_data_models import SatelliteImageMetadata

from src.utils.credentials import CredentialManager
from src.utils.common_utils import get_date_range, get_iso_datetime_format, get_compact_datime_format

import logging

from typing import Union, Optional, Dict, Any, List


def image_path_builder(date: str, location: str) -> str:
    return f'{get_compact_datime_format(date)}_{location}.tiff'


class SentinelHubAuthenticator:
    def __init__(self,
                 credentials: dict,
                 token_path: Optional[Union[Path, str]] = None,
                 logger: Optional[logging.Logger] = None
                 ):
        self.client_id = credentials['client_id']
        self.client_secret = credentials['client_secret']
        self.token_path = token_path or Path(self._init_cache_dir()) / 'sentinelhub_token.json'
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self.oauth = self._client_setup()
        self.token = None

    @staticmethod
    def _init_cache_dir() -> Path:
        """ Initializes and returns the cache directory for storing the auth token.

        :return: path to cache directory for storing token
        """
        cache_dir = Path.home() / '.cache' / 'sentinelhub'
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def _save_token(self, token: dict):
        """ Saves SentinelHub API token to JSON file.

        :param token: SentinelHub API token
        """
        with open(self.token_path, 'w') as f:
            json.dump(token, f)

    def _load_token(self) -> dict:
        """ Loads existing SentinelHub API token.

        :return: token
        """

        with open(self.token_path, 'r') as f:
            token = json.load(f)
        return token

    def _expired_token_check(self) -> bool:
        """ Checks whether the stored token is expired (with a 1-minute buffer).

        :return: True if token is expired
        """
        token_expire_datetime = datetime.fromtimestamp(self.token['expires_at'], tz=pytz.utc)
        return token_expire_datetime <= datetime.now(pytz.utc) + timedelta(minutes=1)

    def _client_setup(self) -> OAuth2Session:
        client = BackendApplicationClient(client_id=self.client_id)
        return OAuth2Session(client=client)

    def authenticate(self):
        """ Handles OAuth2 authentication with SentinelHub. Reuses a stored token if valid, otherwise requests a new one.
        """

        try:
            if self.token_path.exists():
                self.token = self._load_token()
        except (json.JSONDecodeError, PermissionError) as e:
            self.logger.warning(f'Failed to load token, will fetch new one: {e}')
            self.token = None

        if not self.token or self._expired_token_check():
            try:
                self.logger.info('Fetching new token.')
                self.token = self.oauth.fetch_token(
                    token_url='https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token',
                    client_secret=self.client_secret, include_client_id=True)
                if not self.token['access_token']:
                    raise ValueError("Invalid API token. Missing 'access_token' key.")
                self._save_token(self.token)
            except Exception as e:
                self.logger.error(f'Failed to fetch token: {e}')
                raise
        else:
            self.logger.info('Using existing token from file.')
        return self.token, self.oauth


class SentinelImageExtractor:
    def __init__(self,
                 cfg: dict, oauth: OAuth2Session,
                 token: dict,
                 logger: Optional[logging.Logger] = None
                 ):
        self.cfg = cfg
        self.bbox = self._coords_to_bbox()
        self.token = token
        self.oauth = oauth
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def _coords_to_bbox(self):
        coords = self.cfg['location']['coordinates']
        return [coords['min_lon'], coords['min_lat'], coords['max_lon'], coords['max_lat']]

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
                self.logger.error(f'API request failed: {e}')
                raise

        self.logger.info(f'Available dates: {len(all_dates)}')
        return all_dates

    def download_sentinel_image(self, iso_datetime: str) -> bytes:
        """ Fetches a satellite image for a specific datetime using SentinelHub Process API.

        :param iso_datetime: target datetime in ISO format
        :return: Image data in TIFF format
        """
        headers = {
            "Authorization": f"Bearer {self.token['access_token']}",
            "Accept": "image/tiff"
        }

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
            "evalscript": self._default_evalscript()
        }

        self.logger.info(f"Extracting {self.cfg['sentinel_type']} images for ...")
        self.logger.info(f"Location - {self.cfg['location']['name']}")
        self.logger.info(f"Date - {iso_datetime}")
        url = "https://sh.dataspace.copernicus.eu/api/v1/process"
        try:
            response = self.oauth.post(url, json=request, headers=headers)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            self.logger.error(f'Failed to get sentinel images for {iso_datetime}: {e}')
            raise

    def _default_evalscript(self):
        return """
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


class SentinelImageSaver:
    def __init__(self, creds: Dict[str, Any]):
        self.minio_saver = MinIOSaver(creds)

    def bulk_save(self, images_data: List[Dict[str, Any]], bucket_name: str):
        for data in images_data:
            self.minio_saver.save(bucket_name, data['file_name'], data['image'], 'tiff')


class SentinelImageMetadataProcessor:
    def __init__(self, cfg: Dict[str, Any], logger: Optional[logging.Logger] = None):
        self.cfg = cfg
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def process(self, dates: List[str]) -> List[Dict[str, Any]]:
        metadata = []
        for date in dates:
            data = {
                'satellite_type': self.cfg['sentinel_type'],
                'location_name': self.cfg['location']['name'],
                'image_date': date,
                'min_lat': self.cfg['location']['coordinates']['min_lat'],
                'min_lon': self.cfg['location']['coordinates']['min_lon'],
                'max_lat': self.cfg['location']['coordinates']['max_lat'],
                'max_lon': self.cfg['location']['coordinates']['max_lon'],
                'image_path': image_path_builder(date, self.cfg['location']['name'])
            }
            metadata.append(data)
        return metadata
    
    
class SentinelMetadataSaver:
    def __init__(self, creds: dict, logger: Optional[logging.Logger] = None):
        self.postgre_saver = PostgreSaver(creds)
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    @staticmethod
    def _satellite_image_metadata_object(data: Dict[str, Any]) -> SatelliteImageMetadata:
        return SatelliteImageMetadata(
            satellite_type=data['satellite_type'],
            location_name=data['location_name'],
            image_date=data['image_date'],
            min_lat=data['min_lat'],
            min_lon=data['min_lon'],
            max_lat=data['max_lat'],
            max_lon=data['max_lon'],
            image_path=data['image_path']
        )

    # TODO: mechanism to load metadata later (i.e. when PostgreSQL fails)
    def bulk_save(self, image_metadata: List[Dict[str, Any]], db_name: str):
        for data in image_metadata:
            self.postgre_saver.save(db_name, self._satellite_image_metadata_object(data))

        if self.postgre_saver.skipped_rows > 0:
            self.logger.warning(f'Skipped {self.postgre_saver.skipped_rows} rows.')


class SentinelDataPipeline:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.logger = logging.getLogger(self.__class__.__name__)
        self.cred_mgr = CredentialManager()
        self.image_saver = SentinelImageSaver(self.cred_mgr.get_minio_credentials())
        self.metadata_processor = SentinelImageMetadataProcessor(self.cfg)
        self.metadata_saver = SentinelMetadataSaver(self.cred_mgr.get_pg_credentials())

    def run(self, n_days: int = 1):
        """ Executes the full extraction process for the last n_days:

        Authenticates with SentinelHub
        Gets available images
        Downloads and saves each image to MinIO
        Logs metadata to PostgreSQL

        :param n_days: number of days to look back from today
        """
        sentinel_creds = self.cred_mgr.get_sentinelhub_credentials()
        auth = SentinelHubAuthenticator(sentinel_creds, logger=self.logger)
        token, oauth = auth.authenticate()

        service = SentinelImageExtractor(self.cfg, oauth, token, self.logger)

        start_date, end_date = get_date_range(n_days)
        iso_start_date = get_iso_datetime_format(start_date)
        iso_end_date = get_iso_datetime_format(end_date)

        available_dates = service.get_available_dates(iso_start_date, iso_end_date)

        try:
            images_data = []
            bucket_name = 'satellite-images'
            for date in available_dates:
                image = service.download_sentinel_image(date)
                file_name = f"{get_compact_datime_format(date)}_{self.cfg['location']['name']}.tiff"
                images_data.append({'file_name': file_name, 'image': image})

            self.image_saver.bulk_save(images_data, bucket_name)
            images_metadata = self.metadata_processor.process(available_dates)
            self.metadata_saver.bulk_save(images_metadata, 'satellite_image_processing')

        except Exception as e:
            self.logger.error(f'Failed to process and save images: {e}')
