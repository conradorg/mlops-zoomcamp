import argparse
import os
import boto3
import io

import pandas as pd


# ENVIRONMENT VARIABLES
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_S3_BUCKET_NAME = os.getenv("AWS_S3_BUCKET_NAME")
AWS_REGION = os.getenv("AWS_REGION")

def get_object(path: str):
    # create client with access credentials
    s3 = boto3.client(
        service_name="s3",
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    response = s3.get_object(
        Bucket=AWS_S3_BUCKET_NAME,
        Key=path,
    )

    # get raw binary data
    parquet_bytes = io.BytesIO(response['Body'].read())
    df = pd.read_parquet(parquet_bytes, engine='pyarrow')

    return response, df


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("year", type=int)
    parser.add_argument("month", type=int)
    args = parser.parse_args()

    path = f"out/predicted_yellow_{args.year}-{args.month:02d}.parquet"
    response, df = get_object(path)
    print(response)
    print()
    print("content:")
    print(df)

if __name__ == "__main__":
    main()