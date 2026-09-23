-- Stock Prices Table
CREATE TABLE IF NOT EXISTS stock_prices (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(10, 2),
    high DECIMAL(10, 2),
    low DECIMAL(10, 2),
    close DECIMAL(10, 2),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

-- Weather Data Table
CREATE TABLE IF NOT EXISTS weather_data (
    id SERIAL PRIMARY KEY,
    city VARCHAR(50) NOT NULL,
    recorded_date DATE NOT NULL,
    temperature DECIMAL(5, 2),
    feels_like DECIMAL(5, 2),
    humidity INTEGER,
    pressure INTEGER,
    wind_speed DECIMAL(5, 2),
    cloudiness INTEGER,
    description VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(city, recorded_date)
);

-- Stock Analytics Table
CREATE TABLE IF NOT EXISTS stock_analytics (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    price_change DECIMAL(10, 2),
    price_change_percent DECIMAL(10, 4),
    moving_avg_7 DECIMAL(10, 2),
    moving_avg_30 DECIMAL(10, 2),
    volatility DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, date)
);

-- Correlation Analysis Table
CREATE TABLE IF NOT EXISTS correlation_analysis (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    city VARCHAR(50) NOT NULL,
    analysis_date DATE NOT NULL,
    correlation_coefficient DECIMAL(5, 3),
    sample_size INTEGER,
    analysis_type VARCHAR(50),
    findings TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(symbol, city, analysis_date)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_stock_symbol_date
ON stock_prices(symbol, date);

CREATE INDEX IF NOT EXISTS idx_weather_city_date
ON weather_data(city, recorded_date);

-- Latest Stock Prices View
CREATE OR REPLACE VIEW latest_stock_prices AS
SELECT DISTINCT ON (symbol)
    symbol,
    date,
    close,
    volume
FROM stock_prices
ORDER BY symbol, date DESC;

-- Latest Weather View
CREATE OR REPLACE VIEW latest_weather AS
SELECT DISTINCT ON (city)
    city,
    recorded_date,
    temperature,
    humidity,
    description
FROM weather_data
ORDER BY city, recorded_date DESC;