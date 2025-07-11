import datetime
import os
import time
import random
import logging 
import uuid
import pytz
import pandas as pd
import io
import psycopg
import joblib

from prefect import task, flow

from evidently import Report
from evidently import DataDefinition
from evidently import Dataset
from evidently.metrics import ValueDrift, DriftedColumnsCount, MissingValueCount, QuantileValue, MaxValue

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s]: %(message)s")

SEND_TIMEOUT = 0
rand = random.Random()

create_table_statement = """
drop table if exists dummy_metrics;
create table dummy_metrics(
	timestamp timestamp,
	fare_amount__column_quantile_05 float,
	total_amount__max_value float
)
"""

# reference_data = pd.read_parquet('data/reference.parquet')
# with open('models/lin_reg.bin', 'rb') as f_in:
# 	model = joblib.load(f_in)

import requests

begin = datetime.datetime(2024, 3, 1, 0, 0)  # March 1st, 2024

filename="green_tripdata_2024-03.parquet"
path = f"data/{filename}"
if not os.path.isfile(path):
	print("downloading data...")
	url = f"https://d37ci6vzurychx.cloudfront.net/trip-data/{filename}"
	response = requests.get(url, allow_redirects=True)
	os.makedirs("data", exist_ok=True)
	with open(path, "wb") as f:
		f.write(response.content)
print("loading data from file... {path}")

raw_data = pd.read_parquet(path)
print("raw_data.shape", raw_data.shape)

begin = datetime.datetime(2024, 3, 1, 0, 0)
num_features = ['passenger_count', 'trip_distance', 'fare_amount', 'total_amount']
cat_features = ['PULocationID', 'DOLocationID']
data_definition = DataDefinition(
    numerical_columns=num_features + ['prediction'],
    categorical_columns=cat_features,
)

report = Report(metrics = [
    # ValueDrift(column='prediction'),
    # DriftedColumnsCount(),
    # MissingValueCount(column='prediction'),
    QuantileValue(column='fare_amount', quantile=0.5),
	MaxValue(column="total_amount"),
])


CONNECTION_STRING = "host=localhost port=5432 user=postgres password=example"
CONNECTION_STRING_DB = CONNECTION_STRING + " dbname=test"


# @task
def prep_db():
	with psycopg.connect(CONNECTION_STRING, autocommit=True) as conn:
		res = conn.execute("SELECT 1 FROM pg_database WHERE datname='test'")
		if len(res.fetchall()) == 0:
			conn.execute("create database test;")
		with psycopg.connect(CONNECTION_STRING_DB) as conn:
			conn.execute(create_table_statement)

# @task
def calculate_metrics_postgresql(day_of_month):
	date = begin + datetime.timedelta(day_of_month)
	current_data = raw_data[(raw_data.lpep_pickup_datetime >= date) &
		(raw_data.lpep_pickup_datetime < (date + datetime.timedelta(1)))]

	#current_data.fillna(0, inplace=True)
	# current_data['prediction'] = model.predict(current_data[num_features + cat_features].fillna(0))

	current_dataset = Dataset.from_pandas(current_data, data_definition=data_definition)
	# reference_dataset = Dataset.from_pandas(reference_data, data_definition=data_definition)

	run = report.run(reference_data=None, current_data=current_dataset)
	# run = report.run(current_data=current_dataset)

	result = run.dict()

	fare_amount__column_quantile_05 = result['metrics'][0]['value']
	total_amount__max_value = result['metrics'][1]['value']
	print(fare_amount__column_quantile_05)
	print(total_amount__max_value)
	with psycopg.connect(CONNECTION_STRING_DB, autocommit=True) as conn:
		with conn.cursor() as curr:
			curr.execute(
				"insert into dummy_metrics(timestamp, fare_amount__column_quantile_05, total_amount__max_value) values (%s, %s, %s)",
				(date, fare_amount__column_quantile_05, total_amount__max_value)
			)

# @flow
def batch_monitoring_backfill():
	prep_db()

	for day_of_month in range(1, 31+1):
		calculate_metrics_postgresql(day_of_month)

if __name__ == '__main__':
	batch_monitoring_backfill()
