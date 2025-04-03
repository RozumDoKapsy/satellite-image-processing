from minio import Minio
from minio.error import S3Error
from io import BytesIO
import logging


def save_to_minio(creds: dict, bucket_name: str, object_name: str, data: bytes, content_type: str, logger=None):
    if logger is None:
        logger = logging.getLogger('MinioStorage')
        logger.setLevel(logging.INFO)

    client = Minio(
        endpoint=creds['endpoint'],
        access_key=creds['access_key'],
        secret_key=creds['secret_key'],
        secure=False
    )
    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            logger.info(f'Bucket "{bucket_name}" created.')
    except S3Error as e:
        logger.error(f'Error checking/creating bucket "{bucket_name}": {e}')
        return

    bytes_data = BytesIO(data)
    size = len(data)
    try:
        client.put_object(bucket_name, object_name, bytes_data, size, content_type)
        logger.info(f'Image uploaded successfully to {object_name}')
    except S3Error as e:
        logger.error(f'Error uploading image: {e}')
