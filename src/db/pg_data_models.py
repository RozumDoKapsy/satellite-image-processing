from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class SatelliteImageMetadata(Base):
    __tablename__ = 'satellite_images_metadata'

    id = Column(Integer, primary_key=True, autoincrement=True)
    satellite_type = Column(String, nullable=True)
    location_name = Column(String, nullable=False)
    image_date = Column(DateTime, nullable=False)
    min_lat = Column(Float, nullable=False)
    min_lon = Column(Float, nullable=False)
    max_lat = Column(Float, nullable=False)
    max_lon = Column(Float, nullable=False)
    image_path = Column(String, nullable=False)

    def __init__(self, satellite_type, location_name, image_date
                 , min_lat, min_lon, max_lat, max_lon, image_path):
        self.satellite_type = satellite_type
        self.location_name = location_name
        self.image_date = image_date
        self.min_lat = min_lat
        self.min_lon = min_lon
        self.max_lat = max_lat
        self.max_lon = max_lon
        self.image_path = image_path


class WeatherHourly(Base):
    __tablename__ = 'weather_hourly'

    id = Column(Integer, primary_key=True, autoincrement=True)
    location_name = Column(String, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    temperature_2m = Column(Float, nullable=True)
    precipitation = Column(Float, nullable=True)
    rain = Column(Float, nullable=True)
    soil_temperature_0cm = Column(Float, nullable=True)
    soil_moisture_0_to_1cm = Column(Float, nullable=True)
