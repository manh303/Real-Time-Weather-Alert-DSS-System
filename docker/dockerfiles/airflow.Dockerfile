FROM apache/airflow:2.5.1-python3.9

USER root

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# Install Python dependencies
COPY requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

# Copy application code
COPY ingestion/ /opt/airflow/dags/ingestion/
COPY spark-app/ /opt/airflow/dags/spark-app/
COPY scripts/ /opt/airflow/dags/scripts/