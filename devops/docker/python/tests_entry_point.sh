#!/bin/sh

set -e

sleep 5

pip install -U veil_api_client veil_aio_au

cd /opt/veil-vdi/app/common/migrations

alembic upgrade head

cd /opt/veil-vdi/app/web_app/tests

pytest -m 'not broken_runner' --cov=web_app --cov-report=term
