# How to use code with a remote S3 bucket

## Prerequisites
- user with permissions as in used-permissions
- access to the bucket in the permissions
- add aws access key

## copy .env-template as .env and add all needed env variables

## prepare env variables and execute code locally
```
# activate env variables locally
set -a
source .env
set +a
```

```
python starter.py 2023 3
```

## execute code locally with docker with .env file
```
docker build -t duration-prediction-batch:v1 .
docker run --env-file .env -it --rm duration-prediction-batch:v1
```

## test download
```
python s3-test-download.py 2023 5
```