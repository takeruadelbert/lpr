FROM python:3.8-slim

ENV REPO_HOME=/home/lpr
RUN mkdir -p ${REPO_HOME}
COPY . ${REPO_HOME}
WORKDIR ${REPO_HOME}

RUN poetry install --no-dev