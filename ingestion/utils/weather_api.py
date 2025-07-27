import requests
import time
import logging
from typing import Dict, List, Optional
from ingestion.config.settings import WeatherConfig, VIETNAM_PROVINCES

class WeatherAPIClient:
    def __init__(self):
        self.api_key = WeatherConfig.OPENWEATHER_API_KEY
        self.base_url = WeatherConfig.OPENWEATHER_BASE_URL
        self.timeout = WeatherConfig.REQUEST_TIMEOUT
        self.max_retries = WeatherConfig.MAX_RETRIES
        self.retry_delay = WeatherConfig.RETRY_DELAY
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Validate API key
        if not self.api_key:
            raise ValueError("OPENWEATHER_API_KEY is required in environment variables")
    
    def get_weather_data(self, lat: float, lon: float, province_name: str) -> Optional[Dict]:
        """Fetch weather data for a specific location"""
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric',  # Celsius
            'lang': 'vi'  # Vietnamese
        }
        
        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    self.base_url, 
                    params=params, 
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                data = response.json()
                
                # Add metadata
                data['province_name'] = province_name
                data['coordinates'] = {'lat': lat, 'lon': lon}
                data['timestamp'] = int(time.time())
                data['fetch_time'] = time.strftime('%Y-%m-%d %H:%M:%S')
                
                self.logger.info(f"Successfully fetched weather data for {province_name}")
                return data
                
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Attempt {attempt + 1} failed for {province_name}: {str(e)}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error(f"All retries failed for {province_name}")
                    return None
            except Exception as e:
                self.logger.error(f"Unexpected error for {province_name}: {str(e)}")
                return None
    
    def get_all_provinces_weather(self) -> List[Dict]:
        """Fetch weather data for all Vietnam provinces"""
        weather_data = []
        
        self.logger.info("Starting weather data collection for all provinces")
        
        for province in VIETNAM_PROVINCES:
            data = self.get_weather_data(
                province['lat'], 
                province['lon'], 
                province['name']
            )
            
            if data:
                weather_data.append(data)
            
            # Avoid rate limiting
            time.sleep(0.1)
        
        self.logger.info(f"Collected weather data for {len(weather_data)} provinces")
        return weather_data
    
    def is_extreme_weather(self, weather_data: Dict) -> Dict:
        """Check if weather data indicates extreme conditions"""
        alerts = {
            'has_alert': False,
            'alert_types': [],
            'severity': 'normal'
        }
        
        try:
            temp = weather_data.get('main', {}).get('temp', 0)
            humidity = weather_data.get('main', {}).get('humidity', 0)
            wind_speed = weather_data.get('wind', {}).get('speed', 0)
            
            # Temperature alert
            if temp >= WeatherConfig.TEMPERATURE_THRESHOLD:
                alerts['has_alert'] = True
                alerts['alert_types'].append('HIGH_TEMPERATURE')
                alerts['severity'] = 'high' if temp >= 40 else 'medium'
            
            # Low humidity (drought risk)
            if humidity <= WeatherConfig.HUMIDITY_THRESHOLD:
                alerts['has_alert'] = True
                alerts['alert_types'].append('LOW_HUMIDITY')
                if alerts['severity'] == 'normal':
                    alerts['severity'] = 'medium'
            
            # High wind speed
            if wind_speed >= WeatherConfig.WIND_SPEED_THRESHOLD:
                alerts['has_alert'] = True
                alerts['alert_types'].append('HIGH_WIND')
                alerts['severity'] = 'high'
            
        except (KeyError, TypeError) as e:
            self.logger.error(f"Error processing weather data: {e}")
        
        return alerts