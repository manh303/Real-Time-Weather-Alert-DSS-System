from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.mongo.hooks.mongo import MongoHook
from airflow.providers.postgres.hooks.postgres import PostgresHook
import subprocess
import logging

# Default arguments
default_args = {
    'owner': 'weather-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

# Create DAG
dag = DAG(
    'weather_etl_pipeline',
    default_args=default_args,
    description='Weather Data ETL Pipeline',
    schedule_interval=timedelta(minutes=10),  # Run every 10 minutes
    catchup=False,
    max_active_runs=1,
    tags=['weather', 'etl', 'real-time']
)

def collect_weather_data(**context):
    """Task to collect weather data"""
    logging.info("Starting weather data collection...")
    
    try:
        # Run weather collection script
        result = subprocess.run([
            'python', '/opt/airflow/dags/scripts/collect_weather.py'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            logging.info("Weather data collection completed successfully")
            logging.info(f"Output: {result.stdout}")
            return "success"
        else:
            logging.error(f"Weather collection failed: {result.stderr}")
            raise Exception(f"Collection failed with return code {result.returncode}")
            
    except subprocess.TimeoutExpired:
        logging.error("Weather data collection timed out")
        raise Exception("Collection timeout")
    except Exception as e:
        logging.error(f"Error in weather data collection: {str(e)}")
        raise

def start_spark_streaming(**context):
    """Task to start/restart Spark streaming job"""
    logging.info("Starting Spark streaming processor...")
    
    try:
        # Submit Spark job
        result = subprocess.run([
            'spark-submit',
            '--packages', 'org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2',
            '--master', 'spark://spark-master:7077',
            '--deploy-mode', 'client',
            '--executor-memory', '2g',
            '--driver-memory', '1g',
            '/opt/spark-apps/spark_streaming_processor.py'
        ], capture_output=True, text=True, timeout=60)
        
        logging.info("Spark streaming job submitted")
        return "spark_job_submitted"
        
    except Exception as e:
        logging.error(f"Error starting Spark streaming: {str(e)}")
        raise

def check_data_quality(**context):
    """Task to check data quality"""
    logging.info("Checking data quality...")
    
    # Check MongoDB data
    mongo_hook = MongoHook(conn_id='mongodb_default')
    collection = mongo_hook.get_collection('raw_weather_data', 'weather_db')
    
    # Get recent records count
    recent_count = collection.count_documents({
        'timestamp': {'$gte': context['execution_date'].timestamp()}
    })
    
    logging.info(f"Found {recent_count} recent weather records")
    
    if recent_count < 50:  # Expect at least 50 records (for 63 provinces)
        logging.warning(f"Low data volume detected: {recent_count} records")
    
    # Check for data completeness
    incomplete_records = collection.count_documents({
        'timestamp': {'$gte': context['execution_date'].timestamp()},
        '$or': [
            {'main.temp': {'$exists': False}},
            {'main.humidity': {'$exists': False}},
            {'province_name': {'$exists': False}}
        ]
    })
    
    if incomplete_records > 0:
        logging.warning(f"Found {incomplete_records} incomplete records")
    
    return {
        'recent_count': recent_count,
        'incomplete_count': incomplete_records
    }

def generate_alerts(**context):
    """Task to generate and send alerts"""
    logging.info("Checking for weather alerts...")
    
    mongo_hook = MongoHook(conn_id='mongodb_default')
    collection = mongo_hook.get_collection('weather_alerts', 'weather_db')
    
    # Get recent alerts
    recent_alerts = list(collection.find({
        'timestamp': {'$gte': context['execution_date'].timestamp()}
    }))
    
    alert_count = len(recent_alerts)
    logging.info(f"Found {alert_count} weather alerts")
    
    if alert_count > 0:
        # Group alerts by type
        alert_summary = {}
        for alert in recent_alerts:
            alert_types = alert.get('alert_info', {}).get('alert_types', [])
            for alert_type in alert_types:
                if alert_type not in alert_summary:
                    alert_summary[alert_type] = []
                alert_summary[alert_type].append(alert['province_name'])
        
        logging.info(f"Alert summary: {alert_summary}")
        
        # Here you could send notifications (email, Slack, etc.)
        # For now, just log the alerts
    
    return alert_summary

def cleanup_old_data(**context):
    """Task to cleanup old data"""
    logging.info("Cleaning up old data...")
    
    # Calculate cutoff date (keep last 30 days)
    cutoff_date = context['execution_date'] - timedelta(days=30)
    cutoff_timestamp = cutoff_date.timestamp()
    
    # Cleanup MongoDB
    mongo_hook = MongoHook(conn_id='mongodb_default')
    
    collections = ['raw_weather_data', 'weather_alerts', 'extreme_weather']
    total_deleted = 0
    
    for collection_name in collections:
        collection = mongo_hook.get_collection(collection_name, 'weather_db')
        result = collection.delete_many({'timestamp': {'$lt': cutoff_timestamp}})
        deleted_count = result.deleted_count
        total_deleted += deleted_count
        logging.info(f"Deleted {deleted_count} old records from {collection_name}")
    
    # Cleanup PostgreSQL
    postgres_hook = PostgresHook(postgres_conn_id='postgres_default')
    
    cleanup_sql = """
    DELETE FROM weather_statistics 
    WHERE window.start < %s;
    """
    
    postgres_hook.run(cleanup_sql, parameters=[cutoff_date])
    
    logging.info(f"Cleanup completed. Total MongoDB records deleted: {total_deleted}")
    
    return total_deleted

# Define tasks
collect_weather_task = PythonOperator(
    task_id='collect_weather_data',
    python_callable=collect_weather_data,
    dag=dag
)

spark_streaming_task = PythonOperator(
    task_id='start_spark_streaming', 
    python_callable=start_spark_streaming,
    dag=dag
)

data_quality_task = PythonOperator(
    task_id='check_data_quality',
    python_callable=check_data_quality,
    dag=dag
)

alerts_task = PythonOperator(
    task_id='generate_alerts',
    python_callable=generate_alerts,
    dag=dag
)

cleanup_task = PythonOperator(
    task_id='cleanup_old_data',
    python_callable=cleanup_old_data,
    dag=dag
)

# Set task dependencies
collect_weather_task >> spark_streaming_task >> data_quality_task >> alerts_task
data_quality_task >> cleanup_task