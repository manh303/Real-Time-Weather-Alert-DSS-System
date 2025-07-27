-- Initialize PostgreSQL database for Weather DWH

-- Create weather statistics table
CREATE TABLE IF NOT EXISTS weather_statistics (
    id SERIAL PRIMARY KEY,
    province_name VARCHAR(100) NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    avg_temp DECIMAL(5,2),
    max_temp DECIMAL(5,2),
    min_temp DECIMAL(5,2),
    avg_humidity DECIMAL(5,2),
    avg_wind_speed DECIMAL(5,2),
    record_count INTEGER,
    extreme_temp_count INTEGER DEFAULT 0,
    low_humidity_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(province_name, window_start)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_weather_stats_province ON weather_statistics(province_name);
CREATE INDEX IF NOT EXISTS idx_weather_stats_window ON weather_statistics(window_start);
CREATE INDEX IF NOT EXISTS idx_weather_stats_temp ON weather_statistics(avg_temp);

-- Create weather alerts summary table
CREATE TABLE IF NOT EXISTS alert_summary (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    province_name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    alert_count INTEGER DEFAULT 0,
    max_severity VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(date, province_name, alert_type)
);

-- Create indexes for alert summary
CREATE INDEX IF NOT EXISTS idx_alert_summary_date ON alert_summary(date);
CREATE INDEX IF NOT EXISTS idx_alert_summary_province ON alert_summary(province_name);
CREATE INDEX IF NOT EXISTS idx_alert_summary_type ON alert_summary(alert_type);

-- Create view for latest weather statistics
CREATE OR REPLACE VIEW latest_weather_stats AS
SELECT DISTINCT ON (province_name) 
    province_name,
    window_start as last_update,
    avg_temp,
    max_temp,
    min_temp,
    avg_humidity,
    avg_wind_speed,
    extreme_temp_count,
    low_humidity_count
FROM weather_statistics 
ORDER BY province_name, window_start DESC;

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO weather_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO weather_user;