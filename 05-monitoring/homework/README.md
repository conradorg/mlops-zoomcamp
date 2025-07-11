# Homework 5 - Monitoring with evidently and Grafana (with Docker Compose)

learned concepts:
- Docker Compose 
- entering data into SQL databases using psycopg
- evidently
- Grafana Dashboards
    - apparently it is impossible to select automatically a timespan of data for all data points


# What was done:
- used the file evidently_metrics_calculation.py from module 05 and adapted it
    - calculated metrics daily for all entries in green taxi data March 2024 at once
    - for the mentioned metrics it is not necessary to add a prediction column or a reference dataset 
        - if there is a metrics which requires a column "prediction" or "reference_data" (evidently)
    - added metrics to data base 
    - viewed the two metrics with adminer
    - manually added config files for Grafana
        - `./config/grafana_dashboards.yaml` - general config for dashboards (not dashboards themselves)
        - `./config/grafana_datasources.yaml` - config for datasource, e.g. for accessing the PostgreSQL database
    - manually added pgdata directory (as folder and in the docker-compose.yaml)

# Execute Code
- in the directory with the docker-compose.yaml execute: `docker compose up`
- in the same directory execute: `python evidently_metrics_calculation.py`
- go to Grafana http://127.0.0.1:3000
    - add dashboard and panels
        - select the table
        - add panel - add two columns (timestamp + metric), add time series visualization
        - add another panel - table view - aggregation MAX to get the daily maximum value of quantile=0.5 of fare_amounts
    - save dashboard by copying the json (there really is no other way for saving json files directly in Grafana to avoid consistency problems with the json files)