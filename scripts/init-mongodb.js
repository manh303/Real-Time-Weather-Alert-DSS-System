// scripts/init-mongodb.js

// Switch to weather database
db = db.getSiblingDB('weather_db');

// Create collections with validation schemas
print("Creating weather collections...");

// Create raw_weather_data collection
db.createCollection("raw_weather_data", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["timestamp", "location", "temperature", "humidity"],
         properties: {
            timestamp: {
               bsonType: "date",
               description: "must be a date and is required"
            },
            location: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            temperature: {
               bsonType: "number",
               description: "must be a number and is required"
            },
            humidity: {
               bsonType: "number",
               minimum: 0,
               maximum: 100,
               description: "must be a number between 0-100 and is required"
            },
            pressure: {
               bsonType: "number",
               description: "must be a number"
            },
            wind_speed: {
               bsonType: "number",
               minimum: 0,
               description: "must be a non-negative number"
            },
            wind_direction: {
               bsonType: "number",
               minimum: 0,
               maximum: 360,
               description: "must be a number between 0-360"
            },
            weather_condition: {
               bsonType: "string",
               description: "must be a string"
            }
         }
      }
   }
});

// Create weather_alerts collection
db.createCollection("weather_alerts", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["timestamp", "location", "alert_type", "severity", "message"],
         properties: {
            timestamp: {
               bsonType: "date",
               description: "must be a date and is required"
            },
            location: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            alert_type: {
               bsonType: "string",
               enum: ["temperature", "humidity", "wind_speed", "pressure", "severe_weather"],
               description: "must be one of the predefined alert types"
            },
            severity: {
               bsonType: "string",
               enum: ["low", "medium", "high", "critical"],
               description: "must be one of the predefined severity levels"
            },
            message: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            threshold_value: {
               bsonType: "number",
               description: "must be a number"
            },
            actual_value: {
               bsonType: "number",
               description: "must be a number"
            },
            is_resolved: {
               bsonType: "bool",
               description: "must be a boolean"
            }
         }
      }
   }
});

// Create processed_weather_data collection
db.createCollection("processed_weather_data", {
   validator: {
      $jsonSchema: {
         bsonType: "object",
         required: ["date", "location", "avg_temperature", "avg_humidity"],
         properties: {
            date: {
               bsonType: "string",
               pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}$",
               description: "must be a date string in YYYY-MM-DD format"
            },
            location: {
               bsonType: "string",
               description: "must be a string and is required"
            },
            avg_temperature: {
               bsonType: "number",
               description: "must be a number and is required"
            },
            avg_humidity: {
               bsonType: "number",
               minimum: 0,
               maximum: 100,
               description: "must be a number between 0-100 and is required"
            },
            min_temperature: {
               bsonType: "number",
               description: "must be a number"
            },
            max_temperature: {
               bsonType: "number",
               description: "must be a number"
            },
            avg_pressure: {
               bsonType: "number",
               description: "must be a number"
            },
            avg_wind_speed: {
               bsonType: "number",
               minimum: 0,
               description: "must be a non-negative number"
            },
            dominant_weather_condition: {
               bsonType: "string",
               description: "must be a string"
            },
            data_points_count: {
               bsonType: "int",
               minimum: 1,
               description: "must be a positive integer"
            }
         }
      }
   }
});

print("Collections created successfully!");

// Create indexes for better performance
print("Creating indexes...");

// Indexes for raw_weather_data
db.raw_weather_data.createIndex({ "timestamp": 1 }, { name: "timestamp_idx" });
db.raw_weather_data.createIndex({ "location": 1, "timestamp": -1 }, { name: "location_timestamp_idx" });
db.raw_weather_data.createIndex({ "timestamp": 1 }, { name: "ttl_idx", expireAfterSeconds: 2592000 }); // 30 days TTL

// Indexes for weather_alerts
db.weather_alerts.createIndex({ "timestamp": 1 }, { name: "alert_timestamp_idx" });
db.weather_alerts.createIndex({ "location": 1, "alert_type": 1 }, { name: "location_alert_type_idx" });
db.weather_alerts.createIndex({ "severity": 1, "timestamp": -1 }, { name: "severity_timestamp_idx" });
db.weather_alerts.createIndex({ "timestamp": 1 }, { name: "alert_ttl_idx", expireAfterSeconds: 7776000 }); // 90 days TTL

// Indexes for processed_weather_data
db.processed_weather_data.createIndex({ "date": 1, "location": 1 }, { name: "date_location_idx", unique: true });
db.processed_weather_data.createIndex({ "location": 1, "date": -1 }, { name: "location_date_desc_idx" });

print("Indexes created successfully!");

// Insert sample configuration document
db.config.insertOne({
   _id: "alert_thresholds",
   temperature: {
      high: 37,
      low: 0,
      unit: "celsius"
   },
   humidity: {
      low: 25,
      high: 95,
      unit: "percent"
   },
   wind_speed: {
      high: 50,
      unit: "km/h"
   },
   pressure: {
      low: 980,
      high: 1050,
      unit: "hPa"
   },
   updated_at: new Date()
});

// Insert sample locations
db.locations.insertMany([
   {
      _id: "hanoi",
      name: "Hanoi",
      country: "Vietnam",
      coordinates: { lat: 21.0285, lon: 105.8542 },
      timezone: "Asia/Ho_Chi_Minh",
      active: true
   },
   {
      _id: "ho_chi_minh",
      name: "Ho Chi Minh City",
      country: "Vietnam", 
      coordinates: { lat: 10.8231, lon: 106.6297 },
      timezone: "Asia/Ho_Chi_Minh",
      active: true
   },
   {
      _id: "da_nang",
      name: "Da Nang",
      country: "Vietnam",
      coordinates: { lat: 16.0471, lon: 108.2068 },
      timezone: "Asia/Ho_Chi_Minh",
      active: true
   }
]);

print("MongoDB initialization completed!");

// Show collection statistics
print("Collection statistics:");
print("raw_weather_data: " + db.raw_weather_data.countDocuments());
print("weather_alerts: " + db.weather_alerts.countDocuments());
print("processed_weather_data: " + db.processed_weather_data.countDocuments());
print("config: " + db.config.countDocuments());
print("locations: " + db.locations.countDocuments());