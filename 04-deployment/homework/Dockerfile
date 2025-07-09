FROM python:3.12-slim

WORKDIR /app
COPY [ "model.bin", "model.bin" ]

RUN pip install -U pip
RUN pip install pipenv 

COPY [ "Pipfile", "Pipfile.lock", "./" ]
RUN ls -al

RUN pipenv install --system --deploy

# !NEVER! copy the .env file into container, better provide the .env file when the container is run
COPY ["starter.py", "."]

# RUN pipenv run python starter.py
# ENTRYPOINT [ "pipenv", "run", "pip", "freeze" ]
ENTRYPOINT [ "python", "starter.py", "2023", "5" ]

# docker build -t duration-prediction-batch:v1 .
# docker run -it --rm duration-prediction-batch:v1