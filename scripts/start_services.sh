#!/bin/bash

echo "🚀 Starting Weather Alert DSS System..."

# Start Docker services
echo "Starting Docker Compose services..."
docker-compose -f docker/docker-compose.yml up -d

# Wait for services to be ready
echo "Waiting for services to start..."
sleep 30

# Check service health
echo "Checking service health..."
docker-compose -f docker/docker-compose.yml ps

# Create Kafka topics if they don't exist
echo "Creating Kafka topics..."
docker exec weather-kafka kafka-topics --create --topic weather_data --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists
docker exec weather-kafka kafka-topics --create --topic weather_alerts --bootstrap-server localhost:9092 --partitions 3 --replication-factor 1 --if-not-exists

# Test API connection
echo "Testing weather API..."
python scripts/test_ingestion.py

# Start data collection
echo "Starting weather data collection..."
python -m ingestion.crawl_weather_kafka --mode once

# Submit Spark streaming job
echo "Starting Spark streaming..."
docker exec weather-spark-master spark-submit \
    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2 \
    --master spark://spark-master:7077 \
    --deploy-mode client \
    --executor-memory 2g \
    --driver-memory 1g \
    /opt/spark-apps/spark_streaming_processor.py &

echo "✅ All services started successfully!"
echo ""
echo "🌐 Access URLs:"
echo "- Kafka UI: http://localhost:9092"
echo "- Spark Master UI: http://localhost:8080" 
echo "- MongoDB: mongodb://localhost:27017"
echo "- PostgreSQL: localhost:5432"
echo "- Airflow UI: http://localhost:8082 (admin/admin123)"
echo "- Weather Dashboard: http://localhost:5000"
echo ""
echo "📊 Next steps:"
echo "1. Check Airflow DAGs: http://localhost:8082"
echo "2. Monitor Spark jobs: http://localhost:8080"
echo "3. View weather data: http://localhost:5000/api/weather/current"