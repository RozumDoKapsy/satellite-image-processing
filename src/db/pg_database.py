from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.pg_data_models import SatelliteImageMetadata

import logging


def save_to_pg(creds: dict, object: SatelliteImageMetadata, logger=None):
    if logger is None:
        logger = logging.getLogger('PostgreSQL')
        logger.setLevel(logging.INFO)

    DB_URL = f"postgresql://{creds['username']}:{creds['password']}@{creds['hostname']}:5432/satellite_image_processing"
    engine = create_engine(DB_URL)
    Session = sessionmaker(bind=engine)
    session = Session()

    session.add(object)
    session.commit()
    logger.info(f'Satellite Image Metadata saved to: {object.__tablename__}')
    # TODO: error handling
