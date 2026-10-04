-- ============================================================
-- STOCK-WEATHER ANALYTICS
-- Dashboard SQL Queries
-- ============================================================
--
-- Current database architecture:
--
-- stock_prices
--   -> Raw stock market data
--   -> date, symbol, open, high, low, close, volume
--
-- stock_analytics
--   -> Calculated stock metrics
--   -> price_change, price_change_percent
--   -> moving_avg_7, moving_avg_30, volatility, trend
--
-- weather_data
--   -> Historical weather data
--   -> city, recorded_date, temperature, feels_like,
--      humidity, pressure, wind_speed, cloudiness, weather_code
--
-- correlation_analysis
--   -> Weather-stock correlation results
--
-- ============================================================


-- ============================================================
-- QUERY 1: Stock Price + Moving Averages
-- ============================================================

SELECT
    p.date,
    p.symbol,
    p.close,
    a.moving_avg_7,
    a.moving_avg_30
FROM stock_prices p
JOIN stock_analytics a
    ON p.symbol = a.symbol
   AND p.date = a.date
WHERE p.date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY p.date;


-- ============================================================
-- QUERY 2: Stock Price Performance
-- ============================================================

SELECT
    p.symbol,
    COUNT(*) AS trading_days,
    ROUND(MIN(p.close), 2) AS minimum_price,
    ROUND(MAX(p.close), 2) AS maximum_price,
    ROUND(AVG(p.close), 2) AS average_price,
    ROUND(
        ((MAX(p.close) - MIN(p.close)) / NULLIF(MIN(p.close), 0)) * 100,
        2
    ) AS price_range_percent
FROM stock_prices p
WHERE p.date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY p.symbol
ORDER BY p.symbol;


-- ============================================================
-- QUERY 3: Trading Volume
-- ============================================================

SELECT
    date,
    symbol,
    volume
FROM stock_prices
WHERE date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY date;


-- ============================================================
-- QUERY 4: Average Trading Volume
-- ============================================================

SELECT
    symbol,
    ROUND(AVG(volume), 2) AS average_volume,
    MIN(volume) AS minimum_volume,
    MAX(volume) AS maximum_volume
FROM stock_prices
WHERE date >= CURRENT_DATE - INTERVAL '90 days'
GROUP BY symbol
ORDER BY symbol;


-- ============================================================
-- QUERY 5: Stock Volatility
-- ============================================================

SELECT
    date,
    symbol,
    volatility
FROM stock_analytics
WHERE date >= CURRENT_DATE - INTERVAL '90 days'
  AND volatility IS NOT NULL
ORDER BY date;


-- ============================================================
-- QUERY 6: Average Volatility by Stock
-- ============================================================

SELECT
    symbol,
    ROUND(AVG(volatility), 4) AS average_volatility,
    ROUND(MIN(volatility), 4) AS minimum_volatility,
    ROUND(MAX(volatility), 4) AS maximum_volatility
FROM stock_analytics
WHERE volatility IS NOT NULL
GROUP BY symbol
ORDER BY symbol;


-- ============================================================
-- QUERY 7: Latest Stock Prices
-- ============================================================

SELECT
    symbol,
    date,
    close,
    volume
FROM latest_stock_prices
ORDER BY symbol;


-- ============================================================
-- QUERY 8: Weather Data Detail
-- ============================================================

SELECT
    city,
    recorded_date,
    temperature,
    feels_like,
    humidity,
    pressure,
    wind_speed,
    cloudiness
FROM weather_data
ORDER BY city, recorded_date DESC;


-- ============================================================
-- QUERY 9: Weather Summary by City
-- ============================================================

SELECT
    city,
    COUNT(*) AS days_recorded,
    ROUND(AVG(temperature), 2) AS avg_temperature,
    ROUND(AVG(feels_like), 2) AS avg_feels_like,
    ROUND(AVG(humidity), 2) AS avg_humidity,
    ROUND(AVG(pressure), 2) AS avg_pressure,
    ROUND(AVG(wind_speed), 2) AS avg_wind_speed,
    ROUND(AVG(cloudiness), 2) AS avg_cloudiness
FROM weather_data
GROUP BY city
ORDER BY city;


-- ============================================================
-- QUERY 10: Latest Weather by City
-- ============================================================

SELECT
    city,
    recorded_date,
    temperature,
    humidity,
    description
FROM latest_weather
ORDER BY city;


-- ============================================================
-- QUERY 11: Correlation Analysis
-- ============================================================

SELECT
    analysis_date,
    symbol,
    city,
    analysis_type,
    correlation_coefficient,
    sample_size,
    findings
FROM correlation_analysis
ORDER BY analysis_date DESC, symbol, city, analysis_type;


-- ============================================================
-- QUERY 12: Strongest Correlations
-- ============================================================

SELECT
    symbol,
    city,
    analysis_type,
    correlation_coefficient,
    sample_size,
    findings
FROM correlation_analysis
WHERE ABS(correlation_coefficient) >= 0.30
ORDER BY ABS(correlation_coefficient) DESC;


-- ============================================================
-- QUERY 13: Correlation by Stock
-- ============================================================

SELECT
    symbol,
    ROUND(AVG(correlation_coefficient), 4) AS average_correlation,
    ROUND(MAX(correlation_coefficient), 4) AS maximum_correlation,
    ROUND(MIN(correlation_coefficient), 4) AS minimum_correlation,
    COUNT(*) AS correlation_count
FROM correlation_analysis
GROUP BY symbol
ORDER BY symbol;


-- ============================================================
-- QUERY 14: Correlation by City
-- ============================================================

SELECT
    city,
    ROUND(AVG(correlation_coefficient), 4) AS average_correlation,
    ROUND(MAX(correlation_coefficient), 4) AS maximum_correlation,
    ROUND(MIN(correlation_coefficient), 4) AS minimum_correlation,
    COUNT(*) AS correlation_count
FROM correlation_analysis
GROUP BY city
ORDER BY city;


-- ============================================================
-- QUERY 15: Correlation by Analysis Type
-- ============================================================

SELECT
    analysis_type,
    ROUND(AVG(correlation_coefficient), 4) AS average_correlation,
    ROUND(MAX(correlation_coefficient), 4) AS maximum_correlation,
    ROUND(MIN(correlation_coefficient), 4) AS minimum_correlation,
    COUNT(*) AS observation_count
FROM correlation_analysis
GROUP BY analysis_type
ORDER BY ABS(AVG(correlation_coefficient)) DESC;


-- ============================================================
-- QUERY 16: Data Quality - Stock Prices
-- ============================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT symbol) AS unique_symbols,
    COUNT(DISTINCT date) AS unique_dates,
    COUNT(*) - COUNT(close) AS missing_close_values
FROM stock_prices;


-- ============================================================
-- QUERY 17: Data Quality - Weather
-- ============================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT city) AS unique_cities,
    COUNT(DISTINCT recorded_date) AS unique_dates,
    COUNT(*) - COUNT(temperature) AS missing_temperature,
    COUNT(*) - COUNT(humidity) AS missing_humidity
FROM weather_data;


-- ============================================================
-- QUERY 18: Data Quality - Stock Analytics
-- ============================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT symbol) AS unique_symbols,
    COUNT(*) - COUNT(volatility) AS missing_volatility,
    COUNT(*) - COUNT(moving_avg_7) AS missing_moving_avg_7,
    COUNT(*) - COUNT(moving_avg_30) AS missing_moving_avg_30
FROM stock_analytics;


-- ============================================================
-- QUERY 19: Data Quality - Correlations
-- ============================================================

SELECT
    COUNT(*) AS total_rows,
    COUNT(DISTINCT symbol) AS unique_symbols,
    COUNT(DISTINCT city) AS unique_cities,
    COUNT(DISTINCT analysis_type) AS unique_analysis_types,
    COUNT(*) - COUNT(correlation_coefficient) AS missing_correlations
FROM correlation_analysis;


-- ============================================================
-- QUERY 20: Stock Date Coverage
-- ============================================================

SELECT
    symbol,
    MIN(date) AS first_date,
    MAX(date) AS last_date,
    COUNT(*) AS total_records
FROM stock_prices
GROUP BY symbol
ORDER BY symbol;


-- ============================================================
-- QUERY 21: Weather Date Coverage
-- ============================================================

SELECT
    city,
    MIN(recorded_date) AS first_date,
    MAX(recorded_date) AS last_date,
    COUNT(*) AS total_records
FROM weather_data
GROUP BY city
ORDER BY city;


-- ============================================================
-- QUERY 22: Correlation Matrix
-- ============================================================

SELECT
    symbol,
    city,
    analysis_type,
    ROUND(correlation_coefficient, 4) AS correlation,
    sample_size
FROM correlation_analysis
ORDER BY symbol, city, analysis_type;