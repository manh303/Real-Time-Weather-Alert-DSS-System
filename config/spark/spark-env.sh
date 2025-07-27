# docker/config/spark/spark-env.sh

# Java options
export JAVA_HOME=/opt/bitnami/java
export SPARK_MASTER_HOST=spark-master
export SPARK_MASTER_PORT=7077
export SPARK_MASTER_WEBUI_PORT=8080

# Memory settings
export SPARK_WORKER_MEMORY=2g
export SPARK_WORKER_CORES=2
export SPARK_DRIVER_MEMORY=1g
export SPARK_EXECUTOR_MEMORY=2g

# Logging
export SPARK_LOG_DIR=/opt/spark/logs
export SPARK_PID_DIR=/opt/spark/pids

# Python
export PYSPARK_PYTHON=python3
export PYSPARK_DRIVER_PYTHON=python3

# Classpath
export SPARK_CLASSPATH=$SPARK_CLASSPATH:/opt/spark/jars/*

# Additional JVM options
export SPARK_MASTER_OPTS="-Dspark.deploy.defaultCores=2"
export SPARK_WORKER_OPTS="-Dspark.worker.cleanup.enabled=true -Dspark.worker.cleanup.interval=1800"