# satellite-image-processing

## Next-steps
- Create .env to store environmental variables (maybe try airflow variables)
  - refactor CredentialsManager
- Modularize SentinelHub and OpenMeteo pipelines, so that extraction and saving to DB can be separate task
- Create Pipeline Config that contains information about location etc.
- Create DAGs, but run task from CLI (later replace with dbt??)
- Airflow variables to extract data for specific number of days
- Backfilling, handling retries (indempotent tasks)
  - avoid top-level imports, import in functions like
```python
@dag(...)
def ExtractOpenMeteo():
    @task
    def extract():
        # import here
        from src.extractors.open_meteo import OpenMeteoPipeline
        omp = OpenMeteoPipeline(CONFIG)
        omp.run(n_days=5)
    extract()
```
- Deploy Airflow services that I really need (now I have all of them)
- write guide (add to README) for deploying this pipeline
  - include steps for deploying from scratch (like creating specific folder in Airflow etc.)
- write brief description of project (add to README)

### DoD for next-steps
- I have basic pipeline that extracts data from API and stores data in DB (storage), including metadata about images
- The pipeline follow best practice
- README contains project description and guide for deployment

## Further-steps
- Deploy to cloud (check for prices)
- Transform weather data to daily aggregations
- Extract NDVI from images
- Do some correlation between weather and NDVI
- Try some machine learning techniques
