#!/bin/bash
# docker/config/airflow/entrypoint.sh

set -e

# Wait for postgres to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z postgres-airflow 5432; do
  sleep 1
done
echo "PostgreSQL is ready!"

# Wait for Redis to be ready
echo "Waiting for Redis..."
while ! nc -z redis 6379; do
  sleep 1
done
echo "Redis is ready!"

# Initialize the database (only run once)
if [ "$1" = "webserver" ] || [ "$1" = "scheduler" ]; then
    echo "Initializing Airflow database..."
    airflow db init
    
    # Create admin user if it doesn't exist
    echo "Creating admin user..."
    airflow users create --username admin --password admin123 --firstname Admin --lastname User --role Admin --email admin@weather-dss.com || true
fi

# Execute the command
exec airflow "$@"