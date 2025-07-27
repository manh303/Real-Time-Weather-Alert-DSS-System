#!/bin/bash
# docker/config/spark/entrypoint.sh

set -e

# Create necessary directories
mkdir -p /opt/spark/logs
mkdir -p /opt/spark/pids
mkdir -p /opt/spark/checkpoints
mkdir -p /opt/spark/warehouse

# Set permissions
chown -R 1001:1001 /opt/spark/logs
chown -R 1001:1001 /opt/spark/pids
chown -R 1001:1001 /opt/spark/checkpoints
chown -R 1001:1001 /opt/spark/warehouse

# Export environment variables
export SPARK_HOME=/opt/bitnami/spark
export PATH=$SPARK_HOME/bin:$PATH

# Wait for master to be ready if this is a worker
if [ "$SPARK_MODE" = "worker" ]; then
    echo "Waiting for Spark master to be ready..."
    while ! nc -z spark-master 7077; do
        sleep 1
    done
    echo "Spark master is ready!"
fi

# Start Spark
if [ "$SPARK_MODE" = "master" ]; then
    echo "Starting Spark Master..."
    exec $SPARK_HOME/bin/spark-class org.apache.spark.deploy.master.Master \
        --host 0.0.0.0 \
        --port 7077 \
        --webui-port 8080
elif [ "$SPARK_MODE" = "worker" ]; then
    echo "Starting Spark Worker..."
    exec $SPARK_HOME/bin/spark-class org.apache.spark.deploy.worker.Worker \
        spark://spark-master:7077 \
        --cores $SPARK_WORKER_CORES \
        --memory $SPARK_WORKER_MEMORY \
        --webui-port 8081
else
    exec "$@"
fi