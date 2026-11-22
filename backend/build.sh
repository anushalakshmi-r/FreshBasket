#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python -m pip install -r backend/requirements.txt
python backend/manage.py collectstatic --noinput
python backend/manage.py migrate --noinput
python backend/load_data.py
