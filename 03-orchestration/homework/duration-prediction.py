#!/usr/bin/env python
# coding: utf-8

import pickle
from pathlib import Path

import mlflow.sklearn
import mlflow.sklearn
import pandas as pd
import xgboost as xgb

from sklearn.feature_extraction import DictVectorizer
from sklearn.metrics import root_mean_squared_error

import mlflow
from prefect import flow, task
from prefect.context import get_run_context
from dateutil.relativedelta import relativedelta

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("nyc-taxi-experiment")

models_folder = Path('models')
models_folder.mkdir(exist_ok=True)



# @task(retries=3, retry_delay_seconds=2)
def read_dataframe(year, month):
    url = f'https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet'  # yellow this time
    df = pd.read_parquet(url)

    df['duration'] = df.tpep_dropoff_datetime - df.tpep_pickup_datetime
    df.duration = df.duration.dt.total_seconds() / 60

    df = df[(df.duration >= 1) & (df.duration <= 60)]

    categorical = ['PULocationID', 'DOLocationID']
    df[categorical] = df[categorical].astype(str)

    return df


# @task
def create_X(df, dv=None):
    
    categorical = ['PULocationID', 'DOLocationID']
    df[categorical] = df[categorical].astype(str)
    dicts = df[categorical].to_dict(orient='records')

    if dv is None:
        dv = DictVectorizer(sparse=True)
        X = dv.fit_transform(dicts)
    else:
        X = dv.transform(dicts)

    return X, dv


# @task(log_prints=True)
# def train_model(X_train, y_train, X_val, y_val, dv):
def train_model(X_train, y_train, dv):
    mlflow.sklearn.autolog()

    with mlflow.start_run() as run:
        
        from sklearn.linear_model import LinearRegression
        lr = LinearRegression()
        lr.fit(X_train, y_train)

        print(lr.intercept_)
        mlflow.log_params({"intercept_": lr.intercept_})  # not really a hyperparam

        with open("models/preprocessor.b", "wb") as f_out:
            pickle.dump(dv, f_out)
        mlflow.log_artifact("models/preprocessor.b", artifact_path="preprocessor")

        mlflow.sklearn.log_model(lr, artifact_path="models_mlflow")

        return run.info.run_id


# @flow
def run(year: int = None, month: int = None):
    
    # added to tweak values for time from run_context (if not given as params) 
    # - useful for backfilling
    if year is None or month is None:
        ctx = get_run_context()
        ref_date = ctx.flow_run.expected_start_time - relativedelta(months=1)
        year = ref_date.year
        month = ref_date.month


    df_train = read_dataframe(year=year, month=month)

    # next_year = year if month < 12 else year + 1
    # next_month = month + 1 if month < 12 else 1
    # df_val = read_dataframe(year=next_year, month=next_month)

    X_train, dv = create_X(df_train)
    # X_val, _ = create_X(df_val, dv)

    target = 'duration'
    y_train = df_train[target].values
    # y_val = df_val[target].values

    # run_id = train_model(X_train, y_train, X_val, y_val, dv)
    run_id = train_model(X_train, y_train, dv)
    print(f"MLflow run_id: {run_id}")
    return run_id


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Train a model to predict taxi trip duration.')
    parser.add_argument('--year', type=int, required=True, help='Year of the data to train on')
    parser.add_argument('--month', type=int, required=True, help='Month of the data to train on')
    args = parser.parse_args()

    run_id = run(year=args.year, month=args.month)

    with open("run_id.txt", "w") as f:
        f.write(run_id)