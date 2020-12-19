FROM python:3.8-slim

RUN apt-get update && apt-get install curl -y && apt-get install libgl1-mesa-glx -y && apt-get install libglib2.0-0 -y
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

ENV REPO_HOME=/home/lpr
RUN mkdir -p ${REPO_HOME}
COPY . ${REPO_HOME}
WORKDIR ${REPO_HOME}

RUN poetry install --no-dev