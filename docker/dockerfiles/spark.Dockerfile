# docker/dockerfiles/spark.Dockerfile
FROM bitnami/spark:3.3.2

USER root

# Install additional packages
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Download additional JAR files for connectors
RUN wget -O /opt/bitnami/spark/jars/kafka-clients-3.3.0.jar \
    https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.3.0/kafka-clients-3.3.0.jar

RUN wget -O /opt/bitnami/spark/jars/spark-sql-kafka-0-10_2.12-3.3.2.jar \
    https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.3.2/spark-sql-kafka-0-10_2.12-3.3.2.jar

RUN wget -O /opt/bitnami/spark/jars/postgresql-42.5.0.jar \
    https://jdbc.postgresql.org/download/postgresql-42.5.0.jar

RUN wget -O /opt/bitnami/spark/jars/mongo-spark-connector_2.12-10.0.5.jar \
    https://repo1.maven.org/maven2/org/mongodb/spark/mongo-spark-connector_2.12/10.0.5/mongo-spark-connector_2.12-10.0.5.jar

# Create directories
RUN mkdir -p /opt/spark-apps /opt/spark/work-dir /opt/spark/logs

# Set permissions
RUN chown -R 1001:1001 /opt/spark-apps /opt/spark/work-dir /opt/spark/logs
RUN chmod -R 755 /opt/spark-apps /opt/spark/work-dir /opt/spark/logs

# Copy custom Spark configuration
COPY docker/config/spark/ /opt/bitnami/spark/conf/

USER 1001

WORKDIR /opt/spark-apps