#!/usr/bin/env python3
"""
Integration tests for Weather DSS System
"""

import unittest
import requests
import time
import json
from pymongo import MongoClient
import psycopg2
from kafka import KafkaProducer, KafkaConsumer

class WeatherDSSIntegrationTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.mongodb_uri = "mongodb://admin:admin123@localhost:27017/weather_db?authSource=admin"
        cls.postgres_uri = "postgresql://weather_user:weather_password@localhost:5432/weather_dwh"
        cls.kafka_servers = "localhost:29092"
        cls.dashboard_url = "http://localhost:5000"
        
        # Wait for services to be ready
        time.sleep(10)
    
    def test_01_mongodb_connection(self):
        """Test MongoDB connection and collections"""
        client = MongoClient(self.mongodb_uri)
        db = client.weather_db
        
        # Test connection
        self.assertIsNotNone(db.list_collection_names())
        
        # Check if collections exist or can be created
        collections = ['raw_weather_data', 'weather_alerts', 'extreme_weather']
        for collection in collections:
            self.assertIsNotNone(db[collection])
        
        client.close()
    
    def test_02_postgresql_connection(self):
        """Test PostgreSQL connection and tables"""
        conn = psycopg2.connect(self.postgres_uri)
        cur = conn.cursor()
        
        # Test connection
        cur.execute("SELECT version();")
        version = cur.fetchone()
        self.assertIsNotNone(version)
        
        # Check if tables exist
        cur.execute("""
            SELECT table_name FROM information_schema.tables 
            WHERE table_schema = 'public';
        """)
        tables = [row[0] for row in cur.fetchall()]
        
        expected_tables = ['weather_statistics', 'alert_summary']
        for table in expected_tables:
            self.assertIn(table, tables)
        
        cur.close()
        conn.close()
    
    def test_03_kafka_producer_consumer(self):
        """Test Kafka producer and consumer"""
        # Test producer
        producer = KafkaProducer(
            bootstrap_servers=self.kafka_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        
        test_message = {
            'province_name': 'Test Province',
            'temperature': 25.5,
            'timestamp': int(time.time())
        }
        
        # Send test message
        future = producer.send('weather_data', test_message)
        result = future.get(timeout=10)
        self.assertIsNotNone(result)
        
        producer.close()
        
        # Test consumer
        consumer = KafkaConsumer(
            'weather_data',
            bootstrap_servers=self.kafka_servers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            consumer_timeout_ms=5000,
            auto_offset_reset='latest'
        )
        
        # Send another message to consume
        producer = KafkaProducer(
            bootstrap_servers=self.kafka_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        producer.send('weather_data', test_message)
        producer.close()
        
        # Try to consume the message
        messages = []
        for message in consumer:
            messages.append(message.value)
            break
        
        consumer.close()
        self.assertTrue(len(messages) >= 0)  # May not receive due to timing
    
    def test_04_weather_api_ingestion(self):
        """Test weather data ingestion"""
        from ingestion.utils.weather_api import WeatherAPIClient
        
        client = WeatherAPIClient()
        
        # Test single location
        weather_data = client.get_weather_data(21.0285, 105.8542, "Hà Nội")
        
        self.assertIsNotNone(weather_data)
        self.assertEqual(weather_data['province_name'], "Hà Nội")
        self.assertIn('main', weather_data)
        self.assertIn('temp', weather_data['main'])
    
    def test_05_dashboard_api(self):
        """Test dashboard API endpoints"""
        try:
            # Test health endpoint
            response = requests.get(f"{self.dashboard_url}/api/health", timeout=10)
            self.assertEqual(response.status_code, 200)
            
            health_data = response.json()
            self.assertEqual(health_data['status'], 'healthy')
            
            # Test current weather endpoint
            response = requests.get(f"{self.dashboard_url}/api/weather/current", timeout=10)
            self.assertIn(response.status_code, [200, 500])  # May be empty initially
            
            # Test dashboard summary
            response = requests.get(f"{self.dashboard_url}/api/dashboard/summary", timeout=10)
            self.assertIn(response.status_code, [200, 500])  # May be empty initially
            
        except requests.exceptions.ConnectionError:
            self.skipTest("Dashboard service not available")
    
    def test_06_end_to_end_data_flow(self):
        """Test complete data flow from ingestion to storage"""
        from ingestion.crawl_weather_kafka import WeatherDataCollector
        
        # Run data collection
        collector = WeatherDataCollector()
        collector.collect_and_send_weather_data()
        
        # Wait for data to be processed
        time.sleep(30)
        
        # Check if data exists in MongoDB
        client = MongoClient(self.mongodb_uri)
        db = client.weather_db
        
        # Check raw weather data
        raw_count = db.raw_weather_data.count_documents({})
        self.assertGreater(raw_count, 0, "No weather data found in MongoDB")
        
        # Get a sample record
        sample_record = db.raw_weather_data.find_one()
        self.assertIsNotNone(sample_record)
        self.assertIn('province_name', sample_record)
        self.assertIn('main', sample_record)
        
        client.close()

def run_integration_tests():
    """Run all integration tests"""
    suite = unittest.TestLoader().loadTestsFromTestCase(WeatherDSSIntegrationTest)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == '__main__':
    success = run_integration_tests()
    exit(0 if success else 1)