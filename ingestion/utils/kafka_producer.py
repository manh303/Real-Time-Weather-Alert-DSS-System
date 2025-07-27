import json
import logging
from typing import Dict, List
from kafka import KafkaProducer
from kafka.errors import KafkaError
from ingestion.config.settings import KafkaConfig, WeatherConfig
import time

class WeatherKafkaProducer:
    def __init__(self):
        self.producer = None
        self.weather_topic = WeatherConfig.KAFKA_TOPIC_WEATHER
        self.alert_topic = WeatherConfig.KAFKA_TOPIC_ALERTS
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize Kafka producer
        self._init_producer()
    
    def _init_producer(self):
        """Initialize Kafka producer with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.producer = KafkaProducer(**KafkaConfig.PRODUCER_CONFIG)
                self.logger.info("Kafka producer initialized successfully")
                break
            except KafkaError as e:
                self.logger.error(f"Attempt {attempt + 1} failed to create Kafka producer: {e}")
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2)
    
    def send_weather_data(self, weather_data: Dict, partition_key: str = None) -> bool:
        """Send weather data to Kafka topic"""
        if not self.producer:
            self.logger.error("Kafka producer not initialized")
            return False
            
        try:
            future = self.producer.send(
                self.weather_topic,
                value=weather_data,
                key=partition_key
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            
            self.logger.info(
                f"Weather data sent successfully to topic: {record_metadata.topic}, "
                f"partition: {record_metadata.partition}, "
                f"offset: {record_metadata.offset}"
            )
            return True
            
        except KafkaError as e:
            self.logger.error(f"Failed to send weather data: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending weather data: {str(e)}")
            return False
    
    def send_alert_data(self, alert_data: Dict, partition_key: str = None) -> bool:
        """Send alert data to Kafka topic"""
        if not self.producer:
            self.logger.error("Kafka producer not initialized")
            return False
            
        try:
            future = self.producer.send(
                self.alert_topic,
                value=alert_data,
                key=partition_key
            )
            
            record_metadata = future.get(timeout=10)
            
            self.logger.info(
                f"Alert data sent successfully to topic: {record_metadata.topic}, "
                f"partition: {record_metadata.partition}, "
                f"offset: {record_metadata.offset}"
            )
            return True
            
        except KafkaError as e:
            self.logger.error(f"Failed to send alert data: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error sending alert data: {str(e)}")
            return False
    
    def send_batch_data(self, weather_list: List[Dict]) -> Dict:
        """Send batch weather data and alerts"""
        results = {
            'success_count': 0,
            'failed_count': 0,
            'alert_count': 0
        }
        
        # Import here to avoid circular imports
        from ingestion.utils.weather_api import WeatherAPIClient
        
        for weather_data in weather_list:
            province_name = weather_data.get('province_name', 'unknown')
            
            # Send weather data
            if self.send_weather_data(weather_data, partition_key=province_name):
                results['success_count'] += 1
            else:
                results['failed_count'] += 1
            
            # Check for alerts and send if needed
            try:
                client = WeatherAPIClient()
                alert_info = client.is_extreme_weather(weather_data)
                
                if alert_info['has_alert']:
                    alert_data = {
                        'province_name': province_name,
                        'timestamp': weather_data.get('timestamp'),
                        'weather_data': weather_data,
                        'alert_info': alert_info
                    }
                    
                    if self.send_alert_data(alert_data, partition_key=province_name):
                        results['alert_count'] += 1
                        
            except Exception as e:
                self.logger.error(f"Error processing alerts for {province_name}: {str(e)}")
        
        self.logger.info(f"Batch processing completed: {results}")
        return results
    
    def close(self):
        """Close Kafka producer"""
        if self.producer:
            try:
                self.producer.flush()
                self.producer.close()
                self.logger.info("Kafka producer closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing Kafka producer: {str(e)}")