#!/usr/bin/env python3
"""
Spark Structured Streaming processor for weather data - Fixed version
"""

import os
import sys
import tempfile
from pyspark.sql import SparkSession
from pyspark.sql.functions import *
from pyspark.sql.types import *
from utils.spark_utils import SparkUtils

class WeatherStreamProcessor:
    def __init__(self):
        # Configuration from environment variables
        self.kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:29092')
        self.weather_topic = os.getenv('KAFKA_TOPIC_WEATHER', 'weather_data')
        self.alert_topic = os.getenv('KAFKA_TOPIC_ALERTS', 'weather_alerts')
        
        # MongoDB configuration
        self.mongodb_host = os.getenv('MONGODB_HOST', 'mongodb')
        self.mongodb_port = os.getenv('MONGODB_PORT', '27017')
        self.mongodb_user = os.getenv('MONGODB_USER', 'admin')
        self.mongodb_pass = os.getenv('MONGODB_PASSWORD', 'admin123')
        self.mongodb_db = os.getenv('MONGODB_DATABASE', 'weather_db')
        self.mongodb_uri = f"mongodb://{self.mongodb_user}:{self.mongodb_pass}@{self.mongodb_host}:{self.mongodb_port}/{self.mongodb_db}?authSource=admin"

        # PostgreSQL configuration
        self.postgres_host = os.getenv('POSTGRES_HOST', 'postgres')
        self.postgres_port = os.getenv('POSTGRES_PORT', '5432')
        self.postgres_db = os.getenv('POSTGRES_DB', 'weather_dwh')
        self.postgres_user = os.getenv('POSTGRES_USER', 'weather_user')
        self.postgres_pass = os.getenv('POSTGRES_PASSWORD', 'weather_password')
        self.postgres_url = f"jdbc:postgresql://{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        self.postgres_properties = {
            "user": self.postgres_user,
            "password": self.postgres_pass,
            "driver": "org.postgresql.Driver"
        }

        # Create checkpoint directory with proper permissions
        self.checkpoint_base = self._create_checkpoint_dir()

        # Các schema Spark
        self.weather_schema = SparkUtils.get_weather_schema()
        self.alert_schema = SparkUtils.get_alert_schema()

        # Sau khi các thuộc tính cần thiết đã gán, mới gọi tạo spark session
        self.spark = self._create_spark_session()
    
    def _create_checkpoint_dir(self):
        """Create checkpoint directory with proper permissions"""
        try:
            # Try to use the mounted checkpoint directory
            checkpoint_dir = "/opt/spark/checkpoint"
            if os.path.exists(checkpoint_dir) and os.access(checkpoint_dir, os.W_OK):
                return checkpoint_dir
            else:
                # If not accessible, create temp directory
                temp_dir = tempfile.mkdtemp(prefix="spark_checkpoint_")
                print(f"Using temporary checkpoint directory: {temp_dir}")
                return temp_dir
        except Exception as e:
            # Fallback to system temp directory
            temp_dir = tempfile.mkdtemp(prefix="spark_checkpoint_")
            print(f"Fallback to system temp checkpoint directory: {temp_dir}")
            return temp_dir
    
    def _create_spark_session(self):
        """Create Spark session with required configurations"""
        return SparkSession.builder \
            .appName("WeatherStreamProcessor") \
            .config("spark.sql.adaptive.enabled", "true") \
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
            .config("spark.streaming.kafka.maxRatePerPartition", "1000") \
            .config("spark.sql.streaming.checkpointLocation", self.checkpoint_base) \
            .config("spark.jars.packages", 
                    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.3.2,"
                    "org.mongodb.spark:mongo-spark-connector_2.12:3.0.1") \
            .config("spark.mongodb.input.uri", self.mongodb_uri) \
            .config("spark.mongodb.output.uri", self.mongodb_uri) \
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer") \
            .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
            .getOrCreate()
    
    def read_weather_stream(self):
        """Read weather data from Kafka"""
        return self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.kafka_servers) \
            .option("subscribe", self.weather_topic) \
            .option("startingOffsets", "earliest") \
            .option("failOnDataLoss", "false") \
            .option("maxOffsetsPerTrigger", "1000") \
            .load()
    
    def read_alert_stream(self):
        """Read alert data from Kafka"""
        return self.spark \
            .readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", self.kafka_servers) \
            .option("subscribe", self.alert_topic) \
            .option("startingOffsets", "earliest") \
            .option("failOnDataLoss", "false") \
            .option("maxOffsetsPerTrigger", "1000") \
            .load()
    
    def process_weather_data(self, raw_stream):
        """Process raw weather data stream"""
        try:
            # Parse JSON data with error handling
            parsed_stream = raw_stream.select(
                col("key").cast("string").alias("partition_key"),
                col("timestamp").alias("kafka_timestamp"),
                col("value").cast("string").alias("raw_value")
            ).filter(
                col("raw_value").isNotNull() & (col("raw_value") != "")
            )
            
            # Add debug output
            parsed_stream = parsed_stream.withColumn(
                "debug_info", 
                concat(lit("Processing message: "), col("raw_value"))
            )
            
            # Parse JSON
            json_parsed = parsed_stream.select(
                "partition_key",
                "kafka_timestamp", 
                "raw_value",
                from_json(col("raw_value"), self.weather_schema).alias("data")
            ).filter(col("data").isNotNull())
            
            # Flatten the data
            processed_stream = json_parsed.select(
                "partition_key",
                "kafka_timestamp",
                "data.*"
            )
            
            # Add processing timestamp
            processed_stream = processed_stream.withColumn(
                "processed_timestamp", 
                current_timestamp()
            )
            
            # Add derived columns
            enriched_stream = processed_stream.withColumn(
                "temperature_celsius", col("main.temp")
            ).withColumn(
                "humidity_percent", col("main.humidity")
            ).withColumn(
                "wind_speed_mps", col("wind.speed")
            ).withColumn(
                "is_extreme_temp", col("main.temp") >= 37
            ).withColumn(
                "is_low_humidity", col("main.humidity") <= 25
            ).withColumn(
                "is_high_wind", col("wind.speed") >= 50
            ).withColumn(
                "weather_condition", col("weather")[0]["main"]
            ).withColumn(
                "weather_description", col("weather")[0]["description"]
            )
            
            return enriched_stream
            
        except Exception as e:
            print(f"Error in process_weather_data: {str(e)}")
            # Return original stream for debugging
            return raw_stream.select(
                col("key").cast("string").alias("partition_key"),
                col("timestamp").alias("kafka_timestamp"),
                col("value").cast("string").alias("raw_data")
            )
    
    def process_alert_data(self, raw_stream):
        """Process alert data stream"""
        return raw_stream.select(
            col("key").cast("string").alias("partition_key"),
            col("timestamp").alias("kafka_timestamp"),
            from_json(col("value").cast("string"), self.alert_schema).alias("alert_data")
        ).select(
            "partition_key",
            "kafka_timestamp", 
            "alert_data.*"
        ).withColumn(
            "processed_timestamp", 
            current_timestamp()
        )
    
    def write_to_mongodb(self, processed_stream, collection_name):
        """Write stream to MongoDB with better error handling"""
        def write_batch_to_mongo(batch_df, batch_id):
            print(f"Batch {batch_id}: Processing {batch_df.count()} records for collection {collection_name}")
            
            if batch_df.count() > 0:
                try:
                    # Show sample data for debugging
                    print(f"Sample data for batch {batch_id}:")
                    batch_df.show(5, truncate=False)
                    
                    # Convert to JSON format for MongoDB
                    batch_df.write \
                        .format("mongo") \
                        .option("uri", self.mongodb_uri) \
                        .option("database", "weather_db") \
                        .option("collection", collection_name) \
                        .mode("append") \
                        .save()
                    
                    print(f"✅ Batch {batch_id}: Successfully saved {batch_df.count()} records to MongoDB collection {collection_name}")
                    
                except Exception as e:
                    print(f"❌ Error writing batch {batch_id} to MongoDB: {str(e)}")
                    print(f"MongoDB URI: {self.mongodb_uri}")
                    # Print schema for debugging
                    print("DataFrame schema:")
                    batch_df.printSchema()
            else:
                print(f"⚠️ Batch {batch_id}: No data to write to {collection_name}")
        
        # Create unique checkpoint location for each stream
        checkpoint_location = os.path.join(self.checkpoint_base, f"mongodb_{collection_name}")
        
        return processed_stream.writeStream \
            .foreachBatch(write_batch_to_mongo) \
            .option("checkpointLocation", checkpoint_location) \
            .trigger(processingTime='10 seconds') \
            .start()
    
    def write_to_postgres(self, processed_stream, table_name):
        """Write stream to PostgreSQL"""
        def write_batch_to_postgres(batch_df, batch_id):
            if batch_df.count() > 0:
                try:
                    batch_df.write \
                        .jdbc(
                            url=self.postgres_url,
                            table=table_name,
                            mode="append",
                            properties=self.postgres_properties
                        )
                    
                    print(f"Batch {batch_id}: Saved {batch_df.count()} records to PostgreSQL table {table_name}")
                except Exception as e:
                    print(f"Error writing batch {batch_id} to PostgreSQL: {str(e)}")
        
        # Create unique checkpoint location for each stream
        checkpoint_location = os.path.join(self.checkpoint_base, f"postgres_{table_name}")
        
        return processed_stream.writeStream \
            .foreachBatch(write_batch_to_postgres) \
            .option("checkpointLocation", checkpoint_location) \
            .trigger(processingTime='30 seconds') \
            .start()
    
    def create_real_time_aggregations(self, processed_stream):
        """Create real-time aggregations"""
        # Window-based aggregations (10-minute windows)
        windowed_stats = processed_stream \
            .withWatermark("processed_timestamp", "10 minutes") \
            .groupBy(
                window(col("processed_timestamp"), "10 minutes"),
                "province_name"
            ).agg(
                avg("temperature_celsius").alias("avg_temp"),
                max("temperature_celsius").alias("max_temp"),
                min("temperature_celsius").alias("min_temp"),
                avg("humidity_percent").alias("avg_humidity"),
                avg("wind_speed_mps").alias("avg_wind_speed"),
                count("*").alias("record_count"),
                sum(when(col("is_extreme_temp"), 1).otherwise(0)).alias("extreme_temp_count"),
                sum(when(col("is_low_humidity"), 1).otherwise(0)).alias("low_humidity_count")
            )
        
        return windowed_stats
    
    def filter_extreme_weather(self, processed_stream):
        """Filter extreme weather conditions"""
        return processed_stream.filter(
            (col("is_extreme_temp") == True) |
            (col("is_low_humidity") == True) |
            (col("is_high_wind") == True)
        )
    
    def test_kafka_connection(self):
        """Test Kafka connection and show available data"""
        print("Testing Kafka connection...")
        try:
            # Read a small batch to test
            test_df = self.spark \
                .read \
                .format("kafka") \
                .option("kafka.bootstrap.servers", self.kafka_servers) \
                .option("subscribe", self.weather_topic) \
                .option("startingOffsets", "earliest") \
                .option("endingOffsets", "latest") \
                .load()
            
            count = test_df.count()
            print(f"Found {count} messages in topic {self.weather_topic}")
            
            if count > 0:
                print("Sample messages:")
                test_df.select(col("value").cast("string")).show(5, truncate=False)
            
            return count > 0
        except Exception as e:
            print(f"Error testing Kafka connection: {str(e)}")
            return False
    
    def start_processing(self):
        """Start the streaming processing"""
        print("Starting Weather Stream Processing...")
        print(f"Kafka servers: {self.kafka_servers}")
        print(f"Weather topic: {self.weather_topic}")
        print(f"Alert topic: {self.alert_topic}")
        print(f"MongoDB URI: {self.mongodb_uri}")
        print(f"Using checkpoint directory: {self.checkpoint_base}")
        
        # Test Kafka connection first
        if not self.test_kafka_connection():
            print("⚠️ No data found in Kafka topics. Make sure data is being produced.")
            
        try:
            # Read streams
            print("Creating weather stream...")
            weather_stream = self.read_weather_stream()
            
            print("Creating alert stream...")
            alert_stream = self.read_alert_stream()
            
            # Process weather data
            print("Processing weather data...")
            processed_weather = self.process_weather_data(weather_stream)
            
            # Process alert data  
            print("Processing alert data...")
            processed_alerts = self.process_alert_data(alert_stream)
            
            # Write to MongoDB - Start with just raw weather data
            print("Starting MongoDB writer for weather data...")
            weather_writer = self.write_to_mongodb(processed_weather, "raw_weather_data")
            
            print("Starting MongoDB writer for alerts...")
            alert_writer = self.write_to_mongodb(processed_alerts, "weather_alerts")
            
            # Console output for monitoring
            console_checkpoint = os.path.join(self.checkpoint_base, "console_output")
            print("Starting console output for monitoring...")
            console_writer = processed_weather.writeStream \
                .outputMode("append") \
                .format("console") \
                .option("truncate", "false") \
                .option("numRows", 10) \
                .option("checkpointLocation", console_checkpoint) \
                .trigger(processingTime='15 seconds') \
                .start()
            
            print("✅ All streams started successfully!")
            print("Monitoring streams... (Press Ctrl+C to stop)")
            
            # Wait for streams to finish
            weather_writer.awaitTermination()
            
        except KeyboardInterrupt:
            print("🛑 Stopping streams...")
        except Exception as e:
            print(f"❌ Error in stream processing: {str(e)}")
            import traceback
            traceback.print_exc()
            raise e
        finally:
            print("Stopping Spark session...")
            self.spark.stop()

def main():
    try:
        processor = WeatherStreamProcessor()
        processor.start_processing()
    except Exception as e:
        print(f"Failed to start processor: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()