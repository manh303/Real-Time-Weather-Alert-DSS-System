#!/usr/bin/env python3
"""
Main script for collecting weather data and sending to Kafka
"""
import time
import sys
import os
import schedule
import logging
import argparse
from datetime import datetime

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.utils.weather_api import WeatherAPIClient
from ingestion.utils.kafka_producer import WeatherKafkaProducer

class WeatherDataCollector:
    def __init__(self):
        try:
            self.api_client = WeatherAPIClient()
            self.kafka_producer = WeatherKafkaProducer()
        except Exception as e:
            print(f"Error initializing WeatherDataCollector: {e}")
            raise
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def collect_and_send_weather_data(self):
        """Main function to collect and send weather data"""
        try:
            start_time = time.time()
            self.logger.info("Starting weather data collection cycle")
            
            # Collect weather data for all provinces
            weather_data_list = self.api_client.get_all_provinces_weather()
            
            if not weather_data_list:
                self.logger.warning("No weather data collected")
                return
            
            # Send data to Kafka
            results = self.kafka_producer.send_batch_data(weather_data_list)
            
            end_time = time.time()
            duration = end_time - start_time
            
            self.logger.info(
                f"Weather collection cycle completed in {duration:.2f} seconds. "
                f"Results: {results}"
            )
            
        except Exception as e:
            self.logger.error(f"Error in weather data collection: {str(e)}")
            raise
    
    def run_once(self):
        """Run collection once"""
        self.logger.info("Running weather data collection once")
        try:
            self.collect_and_send_weather_data()
        finally:
            self.kafka_producer.close()
    
    def run_scheduler(self, interval_minutes: int = 10):
        """Run collection on schedule"""
        self.logger.info(f"Starting weather data collection scheduler (every {interval_minutes} minutes)")
        
        # Schedule the job
        schedule.every(interval_minutes).minutes.do(self.collect_and_send_weather_data)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")
        except Exception as e:
            self.logger.error(f"Error in scheduler: {str(e)}")
        finally:
            self.kafka_producer.close()

def main():
    parser = argparse.ArgumentParser(description='Weather Data Collector')
    parser.add_argument('--mode', choices=['once', 'schedule'], default='once',
                       help='Run mode: once or schedule')
    parser.add_argument('--interval', type=int, default=10,
                       help='Collection interval in minutes (for schedule mode)')
    
    args = parser.parse_args()
    
    try:
        collector = WeatherDataCollector()
        
        if args.mode == 'once':
            collector.run_once()
        else:
            collector.run_scheduler(args.interval)
            
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()