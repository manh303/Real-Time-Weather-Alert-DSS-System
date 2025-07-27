#!/bin/bash
# scripts/create-kafka-topics.sh

# Wait for Kafka to be ready
echo "Waiting for Kafka to be ready..."
while ! kafka-topics --bootstrap-server kafka:9092 --list >/dev/null 2>&1; do
    echo "Waiting for Kafka..."
    sleep 2
done

echo "Kafka is ready! Creating topics..."

# Create weather_data topic
kafka-topics --bootstrap-server kafka:9092 \
    --create \
    --topic weather_data \
    --partitions 3 \
    --replication-factor 1 \
    --config retention.ms=604800000 \
    --config segment.ms=86400000 \
    --config compression.type=snappy \
    --config cleanup.policy=delete \
    --if-not-exists

echo "Created weather_data topic"

# Create weather_alerts topic
kafka-topics --bootstrap-server kafka:9092 \
    --create \
    --topic weather_alerts \
    --partitions 2 \
    --replication-factor 1 \
    --config retention.ms=2592000000 \
    --config segment.ms=86400000 \
    --config compression.type=snappy \
    --config cleanup.policy=delete \
    --if-not-exists

echo "Created weather_alerts topic"

# Create processed_weather_data topic for Spark streaming
kafka-topics --bootstrap-server kafka:9092 \
    --create \
    --topic processed_weather_data \
    --partitions 2 \
    --replication-factor 1 \
    --config retention.ms=1209600000 \
    --config segment.ms=86400000 \
    --config compression.type=snappy \
    --config cleanup.policy=delete \
    --if-not-exists

echo "Created processed_weather_data topic"

# List all topics to verify
echo "Current topics:"
kafka-topics --bootstrap-server kafka:9092 --list

echo "Kafka topics created successfully!"