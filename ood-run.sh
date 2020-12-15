#!/bin/bash
source venv/bin/activate
export $(cat environment.env | xargs)
python3 src/main.py
