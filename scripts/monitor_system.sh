#!/bin/bash

echo "🔍 Weather DSS System Monitoring..."

# Check Docker containers
echo "=== Docker Container Status ==="
docker-compose -f docker/docker-compose.yml ps

echo ""
echo "=== Kafka Topics ==="
docker exec weather-kafka kafka-topics --list --bootstrap-server localhost:9092

echo ""
echo "=== Recent Kafka Messages ==="
echo "Weather data topic:"
docker exec weather-kafka kafka-console-consumer --topic weather_data --bootstrap-server localhost:9092 --from-beginning --max-messages 5 2>/dev/null || echo "No messages found"

echo ""
echo "=== MongoDB Collections ==="
docker exec weather-mongodb mongosh --eval "
use weather_db; 
db.getCollectionNames().forEach(function(collection) {
    print(collection + ': ' + db[collection].countDocuments());
});
"

echo ""
echo "=== PostgreSQL Tables ==="
docker exec weather-postgres psql -U weather_user -d weather_dwh -c "
SELECT table_name, 
       (SELECT COUNT(*) FROM information_schema.tables t2 WHERE t2.table_name = t1.table_name) as row_count
FROM information_schema.tables t1 
WHERE table_schema = 'public';
"

echo ""
echo "=== System Resources ==="
docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}\t{{.BlockIO}}"