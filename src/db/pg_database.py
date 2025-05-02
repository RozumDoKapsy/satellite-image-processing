from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from src.db.pg_data_models import SatelliteImageMetadata, WeatherHourly

from typing import Union
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

    def save(self, db_name: str, record: Union[SatelliteImageMetadata, WeatherHourly]):
        session = self._create_session(db_name)

        session.add(record)
        try:
            session.commit()
            self.logger.info(f'Record saved to: {record.__tablename__}')
        except IntegrityError as e:
            self.logger.warning(f'Skippping row: {e.orig.diag.message_detail}')
