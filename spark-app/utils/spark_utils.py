import json
from pyspark.sql.functions import *
from pyspark.sql.types import *

class SparkUtils:
    @staticmethod
    def get_weather_schema():
        """Define schema for weather data"""
        return StructType([
            StructField("province_name", StringType(), True),
            StructField("timestamp", LongType(), True),
            StructField("fetch_time", StringType(), True),
            StructField("coordinates", StructType([
                StructField("lat", DoubleType(), True),
                StructField("lon", DoubleType(), True)
            ]), True),
            StructField("main", StructType([
                StructField("temp", DoubleType(), True),
                StructField("feels_like", DoubleType(), True),
                StructField("temp_min", DoubleType(), True),
                StructField("temp_max", DoubleType(), True),
                StructField("pressure", IntegerType(), True),
                StructField("humidity", IntegerType(), True)
            ]), True),
            StructField("wind", StructType([
                StructField("speed", DoubleType(), True),
                StructField("deg", IntegerType(), True)
            ]), True),
            StructField("weather", ArrayType(StructType([
                StructField("id", IntegerType(), True),
                StructField("main", StringType(), True),
                StructField("description", StringType(), True)
            ])), True),
            StructField("clouds", StructType([
                StructField("all", IntegerType(), True)
            ]), True),
            StructField("visibility", IntegerType(), True),
            StructField("name", StringType(), True)
        ])
    
    @staticmethod
    def get_alert_schema():
        """Define schema for alert data"""
        return StructType([
            StructField("province_name", StringType(), True),
            StructField("timestamp", LongType(), True),
            StructField("alert_info", StructType([
                StructField("has_alert", BooleanType(), True),
                StructField("alert_types", ArrayType(StringType()), True),
                StructField("severity", StringType(), True)
            ]), True),
            StructField("weather_data", StringType(), True)  # JSON string
        ])