#!/usr/bin/env python3
"""
Debug script to test Kafka connection and data availability
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import *

def test_kafka_data():
    # Create Spark session
    spark = SparkSession.builder \
        .appName("KafkaDebugTest") \
        .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2") \
        .getOrCreate()
    
    kafka_servers = "kafka:29092"
    topic = "weather_data"
    
    try:
        print(f"Testing Kafka connection to {kafka_servers}, topic: {topic}")
        
        # Read all available data from Kafka topic
        df = spark \
            .read \
            .format("kafka") \
            .option("kafka.bootstrap.servers", kafka_servers) \
            .option("subscribe", topic) \
            .option("startingOffsets", "earliest") \
            .option("endingOffsets", "latest") \
            .load()
        
        total_count = df.count()
        print(f"Total messages in topic '{topic}': {total_count}")
        
        if total_count > 0:
            print("\n=== Sample Messages ===")
            df.select(
                col("key").cast("string").alias("key"),
                col("value").cast("string").alias("value"),
                col("timestamp").alias("kafka_timestamp"),
                col("partition").alias("partition"),
                col("offset").alias("offset")
            ).show(5, truncate=False)
            
            print("\n=== Message Value Samples ===")
            df.select(col("value").cast("string")).show(10, truncate=False)
        else:
            print("❌ No messages found in the topic!")
            print("Make sure your data producer is running and sending data to Kafka.")
    
    except Exception as e:
        print(f"❌ Error connecting to Kafka: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        spark.stop()

if __name__ == "__main__":
    test_kafka_data()