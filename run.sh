#!/bin/bash

export $(cat environment.env | xargs)
poetry run python main.py