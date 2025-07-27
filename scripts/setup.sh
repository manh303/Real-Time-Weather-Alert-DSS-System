#!/bin/bash

echo "🌦️ Setting up Weather Alert DSS System..."

# Create necessary directories
mkdir -p data/{mongodb,postgres,logs}
mkdir -p jars                                                                                                   

# Download required JAR files
echo "Downloading Spark-Kafka connector JARs..."
wget -P jars/ https://repo1.maven.org/maven2/org/apache/spark/spark-sql-kafka-0-10_2.12/3.3.2/spark-sql-kafka-0-10_2.12-3.3.2.jar
wget -P jars/ https://repo1.maven.org/maven2/org/apache/kafka/kafka-clients/3.3.2/kafka-clients-3.3.2.jar

# Set permissions
chmod +x scripts/*.sh

# Install Python dependencies
pip install -r requirements.txt

echo "✅ Setup completed!"
echo "Next steps:"
echo "1. Copy .env.example to .env and fill in your API keys"
echo "2. Run: docker-compose up -d"
echo "3. Test ingestion: python -m ingestion.crawl_weather_kafka --mode once"

#!/bin/bash
# File: /mnt/c/DoAn_FPT_FALL2025/air_quality_dss/docker/setup.sh
# Script to create all required directories and set permissions

echo "Creating directory structure..."

# Base project directory
BASE_DIR="/mnt/c/DoAn_FPT_FALL2025/air_quality_dss/docker"
cd $BASE_DIR

# Create all required directories
mkdir -p scripts
mkdir -p airflow/dags
mkdir -p airflow/logs
mkdir -p airflow/plugins
mkdir -p data/mongodb
mkdir -p data/logs
mkdir -p spark-app
mkdir -p jars

echo "Directory structure created successfully!"

# Set permissions for airflow directories (important for WSL)
chmod 755 airflow/
chmod 755 airflow/dags
chmod 755 airflow/logs  
chmod 755 airflow/plugins

echo "Permissions set successfully!"

# Display directory structure
echo "Directory structure:"
tree -d -L 3 || ls -la

echo "Setup completed! Now you can run: docker-compose up -d"