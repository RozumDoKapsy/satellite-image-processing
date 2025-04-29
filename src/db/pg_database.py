from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.pg_data_models import SatelliteImageMetadata, WeatherHourly

from typing import Union, List
import logging


class PostgreSaver:
    def __init__(self, creds: dict):
        self.creds = creds
        self.logger = logging.getLogger(self.__class__.__name__)

    def _create_session(self, db_name: str):
        db_url = f"postgresql://{self.creds['username']}:{self.creds['password']}@{self.creds['hostname']}:5432/{db_name}"
        engine = create_engine(db_url)
        Session = sessionmaker(bind=engine)
        session = Session()
        return session

    def save_bulk(self, db_name: str, records: List[Union[SatelliteImageMetadata, WeatherHourly]]):
        session = self._create_session(db_name)

        session.add_all(records)
        session.commit()
        self.logger.info(f'{len(records)} records saved to: {records[0].__tablename__}')

    def save_single(self, db_name: str, record: Union[SatelliteImageMetadata, WeatherHourly]):
        session = self._create_session(db_name)

        session.add(record)
        session.commit()
        self.logger.info(f'Record saved to: {record.__tablename__}')
