#!/usr/bin/env python3
"""
System monitoring script for Weather DSS
"""

import time
import json
import requests
import subprocess
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SystemMonitor:
    def __init__(self):
        self.kafka_servers = "localhost:29092"
        self.mongodb_uri = "mongodb://admin:admin123@localhost:27017/"
        self.dashboard_url = "http://localhost:5000"
    
    def check_docker_containers(self):
        """Check Docker container status"""
        logger.info("Checking Docker containers...")
        
        try:
            result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\\t{{.Status}}'], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("\n📦 Docker Containers:")
                print(result.stdout)
                return True
            else:
                logger.error("Failed to get Docker status")
                return False
                
        except Exception as e:
            logger.error(f"Docker check failed: {e}")
            return False
    
    def check_kafka_topics(self):
        """Check Kafka topics and messages"""
        logger.info("Checking Kafka topics...")
        
        try:
            # List topics
            result = subprocess.run([
                'docker', 'exec', 'dev-kafka', 'kafka-topics', 
                '--list', '--bootstrap-server', 'localhost:9092'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                topics = result.stdout.strip().split('\n')
                print(f"\n📨 Kafka Topics: {topics}")
                
                # Check message count for weather_data topic
                if 'weather_data' in topics:
                    self.check_topic_messages('weather_data')
                
                return True
            else:
                logger.error("Failed to list Kafka topics")
                return False
                
        except Exception as e:
            logger.error(f"Kafka check failed: {e}")
            return False
    
    def check_topic_messages(self, topic):
        """Check recent messages in a topic"""
        try:
            result = subprocess.run([
                'docker', 'exec', 'dev-kafka', 'kafka-console-consumer',
                '--topic', topic, '--bootstrap-server', 'localhost:9092',
                '--from-beginning', '--max-messages', '3', '--timeout-ms', '5000'
            ], capture_output=True, text=True)
            
            if result.stdout:
                print(f"Recent messages in {topic}:")
                for line in result.stdout.strip().split('\n')[:3]:
                    try:
                        data = json.loads(line)
                        province = data.get('province_name', 'Unknown')
                        temp = data.get('main', {}).get('temp', 'N/A')
                        print(f"  - {province}: {temp}°C")
                    except:
                        print(f"  - Raw: {line[:100]}...")
            else:
                print(f"No recent messages in {topic}")
                
        except Exception as e:
            logger.error(f"Failed to check topic messages: {e}")
    
    def check_mongodb(self):
        """Check MongoDB collections"""
        logger.info("Checking MongoDB...")
        
        try:
            from pymongo import MongoClient
            
            client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            db = client.weather_db
            
            collections = db.list_collection_names()
            print(f"\n🍃 MongoDB Collections: {collections}")
            
            # Check document counts
            for collection_name in ['raw_weather_data', 'weather_alerts']:
                if collection_name in collections:
                    count = db[collection_name].count_documents({})
                    recent_count = db[collection_name].count_documents({
                        'timestamp': {'$gte': (datetime.now() - timedelta(hours=1)).timestamp()}
                    })
                    print(f"  - {collection_name}: {count} total, {recent_count} in last hour")
            
            client.close()
            return True
            
        except Exception as e:
            logger.error(f"MongoDB check failed: {e}")
            return False
    
    def check_dashboard_api(self):
        """Check dashboard API endpoints"""
        logger.info("Checking dashboard API...")
        
        endpoints = [
            '/api/health',
            '/api/weather/current',
            '/api/dashboard/summary'
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.dashboard_url}{endpoint}", timeout=5)
                
                if response.status_code == 200:
                    print(f"✅ {endpoint}: OK")
                    
                    if endpoint == '/api/dashboard/summary':
                        data = response.json()
                        if 'summary' in data:
                            summary = data['summary']
                            print(f"  - Provinces: {summary.get('total_provinces', 0)}")
                            print(f"  - Recent data: {summary.get('recent_data_points', 0)}")
                            print(f"  - Active alerts: {summary.get('active_alerts', 0)}")
                else:
                    print(f"❌ {endpoint}: {response.status_code}")
                    
            except Exception as e:
                print(f"❌ {endpoint}: {str(e)}")
    
    def get_system_resources(self):
        """Get system resource usage"""
        logger.info("Checking system resources...")
        
        try:
            result = subprocess.run([
                'docker', 'stats', '--no-stream', '--format',
                'table {{.Name}}\\t{{.CPUPerc}}\\t{{.MemUsage}}\\t{{.NetIO}}'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("\n💻 System Resources:")
                print(result.stdout)
                return True
            else:
                logger.error("Failed to get system stats")
                return False
                
        except Exception as e:
            logger.error(f"System resource check failed: {e}")
            return False
    
    def run_health_check(self):
        """Run complete health check"""
        print("🏥 Weather DSS System Health Check")
        print("=" * 50)
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 50)
        
        checks = [
            ("Docker Containers", self.check_docker_containers),
            ("Kafka Topics", self.check_kafka_topics),
            ("MongoDB", self.check_mongodb),
            ("Dashboard API", self.check_dashboard_api),
            ("System Resources", self.get_system_resources)
        ]
        
        results = []
        for check_name, check_func in checks:
            print(f"\n🔍 {check_name}...")
            try:
                result = check_func()
                results.append((check_name, result))
            except Exception as e:
                logger.error(f"{check_name} failed: {e}")
                results.append((check_name, False))
        
        # Summary
        print("\n" + "=" * 50)
        print("HEALTH CHECK SUMMARY")
        print("=" * 50)
        
        passed = 0
        for check_name, result in results:
            status = "✅ HEALTHY" if result else "❌ UNHEALTHY"
            print(f"{check_name:<20}: {status}")
            if result:
                passed += 1
        
        print(f"\nOverall Status: {passed}/{len(results)} checks passed")
        
        if passed == len(results):
            print("🎉 System is healthy!")
        else:
            print("⚠️  Some components need attention.")

def main():
    """Main function"""
    monitor = SystemMonitor()
    monitor.run_health_check()

if __name__ == "__main__":
    main()