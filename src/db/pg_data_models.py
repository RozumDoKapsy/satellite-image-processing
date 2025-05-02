from sqlalchemy import Column, Integer, String, Float, DateTime, UniqueConstraint
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

    __table_args__ = (UniqueConstraint(image_date, min_lat, min_lon, max_lat, max_lon),)


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

    __table_args__ = (UniqueConstraint(latitude, longitude, timestamp),)
