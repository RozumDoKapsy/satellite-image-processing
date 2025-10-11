from minio import Minio
from minio.error import S3Error
from io import BytesIO

from typing import Dict, Optional

import logging


class MinIOSaver:
    def __init__(self, creds: Dict[str, str], logger: Optional[logging.Logger] = None):
        self.client = Minio(
            endpoint=creds['endpoint'],
            access_key=creds['access_key'],
            secret_key=creds['secret_key'],
            secure=False
        )
        self.logger = logger or logging.getLogger(self.__class__.__name__)

    def save(self, bucket_name: str, object_name: str, data: bytes, content_type: str):
        try:
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                self.logger.info(f"Bucket '{bucket_name}' created.")
        except S3Error as e:
            self.logger.error(f"Error checking/creating bucket '{bucket_name}': {e}")
            self.logger.exception('Upload failed.')

        bytes_data = BytesIO(data)
        size = len(data)
        try:
            self.client.put_object(bucket_name, object_name, bytes_data, size, content_type)
            self.logger.info(f'Image uploaded successfully to {object_name}.')
        except S3Error as e:
            self.logger.error(f'Error uploading image: {e}')
