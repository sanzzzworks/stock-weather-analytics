DROP TABLE IF EXISTS correlation_analysis;

CREATE TABLE correlation_analysis (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    city VARCHAR(50) NOT NULL,
    analysis_date DATE NOT NULL,
    correlation_coefficient DECIMAL(6, 4),
    sample_size INTEGER,
    analysis_type VARCHAR(100),
    findings TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(symbol, city, analysis_date, analysis_type)
);