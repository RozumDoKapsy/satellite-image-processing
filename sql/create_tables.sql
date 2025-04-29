CREATE TABLE IF NOT EXISTS satellite_images_metadata (
    id SERIAL PRIMARY KEY,
    satellite_type VARCHAR,
    location_name VARCHAR NOT NULL,
    image_date TIMESTAMP NOT NULL,
    min_lat FLOAT NOT NULL,
    min_lon FLOAT NOT NULL,
    max_lat FLOAT NOT NULL,
    max_lon FLOAT NOT NULL,
    image_path VARCHAR NOT NULL,
    extraction_date DATE NOT NULL
);

CREATE TABLE IF NOT EXISTS weather_hourly (
   id SERIAL PRIMARY KEY,
   location_name VARCHAR NOT NULL,
   latitude FLOAT NOT NULL,
   longitude FLOAT NOT NULL,
   timestamp TIMESTAMP NOT NULL,
   temperature_2m FLOAT,
   precipitation FLOAT,
   rain FLOAT,
   soil_temperature_0cm FLOAT,
   soil_moisture_0_to_1cm FLOAT,
   extraction_date DATE NOT NULL
);