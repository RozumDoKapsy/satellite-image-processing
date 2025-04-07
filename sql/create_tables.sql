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