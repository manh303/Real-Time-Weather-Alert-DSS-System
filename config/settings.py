# config/settings.py

KAFKA_BROKER = 'localhost:9092'
KAFKA_TOPIC = 'weather_data'

MONGODB_URI = 'mongodb://localhost:27017'
MONGO_DB = 'air_quality_db'
MONGO_COLLECTION = 'aqi_records'

import json
import os

# Đường dẫn tuyệt đối tới file JSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROVINCE_FILE = os.path.join(BASE_DIR, "vn_provinces_weather_coords.json")

with open(PROVINCE_FILE, "r", encoding="utf-8") as f:
    CITY_COORDS = json.load(f)

OPENWEATHER_API_KEY = 'e0728e28d57c603019f22420e5b0c717'