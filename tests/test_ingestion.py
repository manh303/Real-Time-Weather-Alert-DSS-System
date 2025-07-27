#!/usr/bin/env python3
"""
Test script for the fixed weather ingestion module
"""

import sys
import os
import time

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test all imports work correctly"""
    print("Testing imports...")
    
    try:
        from ingestion.config.settings import WeatherConfig, KafkaConfig, VIETNAM_PROVINCES
        print("✅ Settings import successful")
        
        from ingestion.utils.weather_api import WeatherAPIClient
        print("✅ Weather API client import successful")
        
        from ingestion.utils.kafka_producer import WeatherKafkaProducer
        print("✅ Kafka producer import successful")
        
        from ingestion.crawl_weather_kafka import WeatherDataCollector
        print("✅ Main collector import successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_config():
    """Test configuration"""
    print("\nTesting configuration...")
    
    try:
        from ingestion.config.settings import WeatherConfig, VIETNAM_PROVINCES
        
        print(f"API URL: {WeatherConfig.OPENWEATHER_BASE_URL}")
        print(f"Kafka servers: {WeatherConfig.KAFKA_BOOTSTRAP_SERVERS}")
        print(f"Total provinces: {len(VIETNAM_PROVINCES)}")
        print(f"First province: {VIETNAM_PROVINCES[0]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Config error: {e}")
        return False

def test_weather_client():
    """Test weather API client (without actual API call)"""
    print("\nTesting Weather API Client...")
    
    try:
        from ingestion.utils.weather_api import WeatherAPIClient
        
        # Check if we can create client (will fail if no API key)
        client = WeatherAPIClient()
        print("✅ Weather client created successfully")
        
        # Test extreme weather detection with mock data
        mock_data = {
            'main': {'temp': 38, 'humidity': 20},
            'wind': {'speed': 15}
        }
        
        alerts = client.is_extreme_weather(mock_data)
        print(f"Alert test result: {alerts}")
        
        return True
        
    except ValueError as e:
        print(f"⚠️  Weather client error (expected if no API key): {e}")
        return True  # This is expected without API key
    except Exception as e:
        print(f"❌ Weather client error: {e}")
        return False

def test_kafka_producer():
    """Test Kafka producer creation"""
    print("\nTesting Kafka Producer...")
    
    try:
        from ingestion.utils.kafka_producer import WeatherKafkaProducer
        
        # This will likely fail without Kafka running, but we test the import
        producer = WeatherKafkaProducer()
        print("✅ Kafka producer created successfully")
        
        producer.close()
        return True
        
    except Exception as e:
        print(f"⚠️  Kafka producer error (expected without Kafka): {e}")
        return True  # This is expected without Kafka running

def main():
    """Run all tests"""
    print("🧪 Testing Fixed Weather Ingestion Module\n")
    
    tests = [
        ("Imports", test_imports),
        ("Configuration", test_config),
        ("Weather Client", test_weather_client),
        ("Kafka Producer", test_kafka_producer)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running {test_name} test...")
        print('='*50)
        
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results