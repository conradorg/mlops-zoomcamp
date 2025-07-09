#!/usr/bin/env python
# coding: utf-8

import io
import os

import argparse
import pickle
import pandas as pd

import boto3


# ENVIRONMENT VARIABLES
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")



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


def prepare_result_df(df, y_pred):
    df_result = pd.DataFrame()
    df_result['ride_id'] = df['ride_id']
    df_result['predicted_duration'] = y_pred
    return df_result


def save_result(year, month, df_result: pd.DataFrame):
    os.makedirs("out", exist_ok=True)
    out_path = f"out/predicted_yellow_{year}-{month:02d}.parquet"

    df_result.to_parquet(
        out_path,
        engine='pyarrow',
        compression=None,
        index=False
    )
    return out_path


def upload_result_s3(year, month, df_result: pd.DataFrame):
    out_path = f"out/predicted_yellow_{year}-{month:02d}.parquet"

    # write file to buffer
    buffer = io.BytesIO()  # create memory buffer for parquet file
    df_result.to_parquet(buffer, index=False, engine='pyarrow')
    buffer.seek(0)  # reset back to start of buffer

    # create client with access credentials
    s3 = boto3.client(
        service_name="s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    response = s3.put_object(
        Bucket=AWS_S3_BUCKET_NAME,
        Key=out_path,
        Body=buffer.getvalue(),
        ContentType='application/octet-stream'  # content type for unknown or binary type (parquet)
    )
    return response


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int)
    parser.add_argument("month", type=int)
    args = parser.parse_args()

    print(f"downloading and reading data for {args.year} {args.month}...")
    df = read_data_year_month(args.year, args.month)

    print(f"preprocessing data...")
    dicts = preprocess_data(df)
    
    print(f"load model...")
    dv, model = load_model()

    print(f"predicting...")
    X_val = dv.transform(dicts)
    y_pred = model.predict(X_val)
    

    print(pd.DataFrame(y_pred).mean())
    print("preparing result...")
    df_result = prepare_result_df(df, y_pred)

    print(f"saving result locally...")
    out_path = save_result(args.year, args.month, df_result)
    print(f"\t saved to {out_path}")

    print(f"uploading results to bucket <{AWS_S3_BUCKET_NAME}>...")
    response = upload_result_s3(args.year, args.month, df_result)
    print(f"response from bucket: \n{response}")


if __name__ == "__main__":
    main()

