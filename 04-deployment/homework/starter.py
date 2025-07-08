#!/usr/bin/env python
# coding: utf-8

import os

import argparse
import pickle
import pandas as pd


categorical = ['PULocationID', 'DOLocationID']


def read_data(filename):
    df = pd.read_parquet(filename)

    df['duration'] = df.tpep_dropoff_datetime - df.tpep_pickup_datetime
    df['duration'] = df.duration.dt.total_seconds() / 60

    df = df[(df.duration >= 1) & (df.duration <= 60)].copy()

    df[categorical] = df[categorical].fillna(-1).astype('int').astype('str')

    return df


def read_data_year_month(year: int, month: int):
    df = read_data(f'https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_{year}-{month:02d}.parquet')
    
    # in fact this could also count as preprocessing
    df['ride_id'] = f'{year:04d}/{month:02d}_' + df.index.astype('str')
    return df


def preprocess_data(df):
    dicts = df[categorical].to_dict(orient='records')
    return dicts


def load_model():
    with open('model.bin', 'rb') as f_in:
        dv, model = pickle.load(f_in)
    return dv, model


def save_result(year, month, df, y_pred):
    os.makedirs("out", exist_ok=True)
    output_file = f"out/predicted_yellow_{year}-{month:02d}.parquet"

    df_result = pd.DataFrame()
    df_result['ride_id'] = df['ride_id']
    df_result['predicted_duration'] = y_pred
    df_result.to_parquet(
        output_file,
        engine='pyarrow',
        compression=None,
        index=False
    )
    print(df_result)




def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int)
    parser.add_argument("month", type=int)
    args = parser.parse_args()

    df = read_data_year_month(args.year, args.month)

    dicts = preprocess_data(df)
    
    dv, model = load_model()

    X_val = dv.transform(dicts)
    y_pred = model.predict(X_val)
    
    print(pd.DataFrame(y_pred).mean())


if __name__ == "__main__":
    main()

