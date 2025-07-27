from flask import Flask, jsonify, request
from flask_cors import CORS
import os
from datetime import datetime, timedelta
from pymongo import MongoClient
import psycopg2
from psycopg2.extras import RealDictCursor
import logging

app = Flask(__name__)
CORS(app)

# Configuration
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://admin:admin123@localhost:27017/weather_db?authSource=admin')
POSTGRES_URI = os.getenv('POSTGRES_URI', 'postgresql://weather_user:weather_password@localhost:5432/weather_dwh')

# MongoDB connection
mongo_client = MongoClient(MONGODB_URI)
mongo_db = mongo_client.weather_db

# PostgreSQL connection
def get_postgres_connection():
    return psycopg2.connect(POSTGRES_URI)

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'mongodb': 'connected',
            'postgresql': 'connected'
        }
    })

@app.route('/api/weather/current')
def get_current_weather():
    """Get current weather data for all provinces"""
    try:
        # Get latest weather data from MongoDB
        pipeline = [
            {'$sort': {'timestamp': -1}},
            {'$group': {
                '_id': '$province_name',
                'latest_data': {'$first': '$ROOT'}
            }},
            {'$replaceRoot': {'newRoot': '$latest_data'}},
            {'$project': {
                'province_name': 1,
                'temperature': '$main.temp',
                'humidity': '$main.humidity', 
                'wind_speed': '$wind.speed',
                'weather_condition': {'$arrayElemAt': ['$weather.main', 0]},
                'weather_description': {'$arrayElemAt': ['$weather.description', 0]},
                'timestamp': 1,
                'coordinates': 1
            }}
        ]
        
        current_weather = list(mongo_db.raw_weather_data.aggregate(pipeline))
        
        return jsonify({
            'success': True,
            'data': current_weather,
            'count': len(current_weather)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weather/alerts')
def get_weather_alerts():
    """Get current weather alerts"""
    try:
        # Get recent alerts (last 24 hours)
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        alerts = list(mongo_db.weather_alerts.find({
            'timestamp': {'$gte': cutoff_time.timestamp()}
        }).sort('timestamp', -1))
        
        # Convert ObjectId to string for JSON serialization
        for alert in alerts:
            alert['_id'] = str(alert['_id'])
        
        return jsonify({
            'success': True,
            'data': alerts,
            'count': len(alerts)
        })
        
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': str(e)
        }), 500

@app.route('/api/weather/statistics')
def get_weather_statistics():
    """Get weather statistics from PostgreSQL"""
    try:
        hours = request.args.get('hours', 24, type=int)
        
        with get_postgres_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                query = """
                SELECT 
                    province_name,
                    AVG(avg_temp) as avg_temperature,
                    MAX(max_temp) as max_temperature,
                    MIN(min_temp) as min_temperature,
                    AVG(avg_humidity) as avg_humidity,
                    AVG(avg_wind_speed) as avg_wind_speed,
                    SUM(extreme_temp_count) as total_extreme_temp,
                    SUM(low_humidity_count) as total_low_humidity,
                    COUNT(*) as data_points
                FROM weather_statistics 
                WHERE window_start >= NOW() - INTERVAL '%s hours'
                GROUP BY province_name
                ORDER BY avg_temperature DESC;
                """
                
                cur.execute(query, (hours,))
                statistics = cur.fetchall()
        
        return jsonify({
            'success': True,
            'data': [dict(row) for row in statistics],
            'period_hours': hours
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weather/trends/<province_name>')
def get_weather_trends(province_name):
    """Get weather trends for a specific province"""
    try:
        hours = request.args.get('hours', 24, type=int)
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        # Get historical data from MongoDB
        weather_data = list(mongo_db.raw_weather_data.find({
            'province_name': province_name,
            'timestamp': {'$gte': cutoff_time.timestamp()}
        }).sort('timestamp', 1))
        
        # Format data for time series
        trends = []
        for data in weather_data:
            trends.append({
                'timestamp': data['timestamp'],
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'wind_speed': data.get('wind', {}).get('speed', 0),
                'pressure': data['main'].get('pressure', 0)
            })
        
        return jsonify({
            'success': True,
            'province': province_name,
            'data': trends,
            'count': len(trends)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/weather/extreme')
def get_extreme_weather():
    """Get extreme weather events"""
    try:
        days = request.args.get('days', 7, type=int)
        cutoff_time = datetime.now() - timedelta(days=days)
        
        extreme_weather = list(mongo_db.extreme_weather.find({
            'timestamp': {'$gte': cutoff_time.timestamp()}
        }).sort('timestamp', -1))
        
        # Convert ObjectId to string
        for event in extreme_weather:
            event['_id'] = str(event['_id'])
        
        return jsonify({
            'success': True,
            'data': extreme_weather,
            'count': len(extreme_weather),
            'period_days': days
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/dashboard/summary')
def get_dashboard_summary():
    """Get dashboard summary statistics"""
    try:
        # Get current counts
        total_provinces = mongo_db.raw_weather_data.distinct('province_name')
        
        # Get recent data count (last hour)
        recent_cutoff = datetime.now() - timedelta(hours=1)
        recent_data_count = mongo_db.raw_weather_data.count_documents({
            'timestamp': {'$gte': recent_cutoff.timestamp()}
        })
        
        # Get active alerts count
        alert_cutoff = datetime.now() - timedelta(hours=6)
        active_alerts_count = mongo_db.weather_alerts.count_documents({
            'timestamp': {'$gte': alert_cutoff.timestamp()}
        })
        
        # Get extreme weather count (last 24 hours)
        extreme_cutoff = datetime.now() - timedelta(hours=24)
        extreme_count = mongo_db.extreme_weather.count_documents({
            'timestamp': {'$gte': extreme_cutoff.timestamp()}
        })
        
        return jsonify({
            'success': True,
            'summary': {
                'total_provinces': len(total_provinces),
                'recent_data_points': recent_data_count,
                'active_alerts': active_alerts_count,
                'extreme_events_24h': extreme_count,
                'last_updated': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)