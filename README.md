# 🌦️ Real-Time Weather Alert DSS System

> A Big Data Decision Support System (DSS) for monitoring and alerting extreme weather conditions in Vietnam using real-time data.

---

## 📌 Project Overview

This project builds a **real-time decision support system (DSS)** that collects, processes, and stores weather data across 63 provinces in Vietnam. It alerts users about extreme weather events like **heatwaves** (temperature ≥ 37°C) and **drought conditions** (humidity ≤ 25%).

### 🔥 Key Features:
- Collect real-time weather data from OpenWeatherMap API
- Stream data using **Apache Kafka**
- Process and filter critical data using **Apache Spark Streaming**
- Store raw and filtered data in **MongoDB**
- Automate the workflow using **Apache Airflow**
- Containerized deployment with **Docker Compose**

---

## 🎯 Project Objectives

- Build a scalable architecture using Big Data technologies
- Demonstrate real-time stream processing and alerting
- Provide a foundation for weather-based decision making and forecasting

---

## 🧰 Technologies Used

| Component         | Technology                |
|------------------|---------------------------|
| Data Ingestion    |  OpenWeatherMap API |
| Message Queue     | Apache Kafka              |
| Stream Processing | Apache Spark Structured Streaming |
| NoSQL Storage     | MongoDB                   |
| Orchestration     | Apache Airflow            |
| Containerization  | Docker + Docker Compose   |
| (Optional) DWH     | PostgreSQL                |
| (Optional) Dashboard | Flask and React|

---

## 📁 Project Structure
weather-alert-dss/
├── airflow/ # DAGs & configs for Airflow pipeline
├── docker/ # Docker config files
│ ├── docker-compose.yml
│ └── .env
├── spark-app/ # Spark Streaming processing scripts
│ └── spark_streaming_processor.py
├── ingestion/ # Weather data collection scripts
│ └── crawl_weather_kafka.py
├── data/ # Mount points for MongoDB and output logs
│ └── db/
├── jars/ # Kafka-Spark JARs
│ └── spark-sql-kafka-0-10_2.12-3.3.2.jar
├── dags/ # Airflow DAG scripts
│ └── weather_etl_dag.py
├── output/ # Exported logs, charts, PDFs
├── requirements.txt # Python dependencies
├── README.md # Project documentation
└── .env # Environment variables

1. **Ingestion**  
   Script `crawl_weather_kafka.py` calls OpenWeatherMap API for 63 provinces and pushes results into Kafka topic `weather_data`.

2. **Streaming Processing**  
   `spark_streaming_processor.py` consumes Kafka stream, parses JSON data, and filters alerts (e.g., temp ≥ 37°C).

3. **Storage**  
   - All data is saved into MongoDB.
   - Can be extended to store into PostgreSQL for reporting.

4. **Orchestration**  
   - Apache Airflow schedules the crawling & processing every N minutes.
   - DAG `weather_etl_dag.py` automates the full pipeline.
