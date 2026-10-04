# data_processing/etl_pipeline.py
import pandas as pd
import os
import sys
from datetime import datetime
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_storage.db_connection import DatabaseConnection
from transformations import (
    StockAnalytics, WeatherAnalytics, DataCleaner, CorrelationAnalysis
)
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ETLPipeline:
    """
    Extract → Transform → Load Pipeline
    
    Orchestrates the complete data processing workflow
    """
    
    def __init__(self, db_connection):
        self.db = db_connection
        self.logger = logger
    
    def extract_stock_data(self, symbol):
        """
        Extract stock data from database
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
        
        Returns:
            DataFrame with stock data
        """
        self.logger.info(f"📤 Extracting stock data for {symbol}...")
        
        query = """
            SELECT symbol, date, open, high, low, close, volume
            FROM stock_prices
            WHERE symbol = %s
            ORDER BY date ASC
        """
        
        results = self.db.query(query, (symbol,))
        df = pd.DataFrame(results)
        
        self.logger.info(f"   Extracted {len(df)} records")
        
        return df
    
    def extract_weather_data(self, city):
        """Extract weather data for a city"""
        
        self.logger.info(f"🌤️ Extracting weather data for {city}...")
        
        query = """
            SELECT city, recorded_date, temperature, feels_like, 
                   humidity, pressure, wind_speed, cloudiness, description
            FROM weather_data
            WHERE city = %s
            ORDER BY recorded_date ASC
        """
        
        results = self.db.query(query, (city,))
        df = pd.DataFrame(results)
        
        self.logger.info(f"   Extracted {len(df)} records")
        
        return df
    
    def transform_stock_data(self, df):
        """
        Transform stock data - add calculated metrics
        
        Args:
            df: Raw stock DataFrame
        
        Returns:
            Transformed DataFrame with new columns
        """
        self.logger.info("🔄 Transforming stock data...")
        
        try:
            # Clean data
            df = DataCleaner.clean_stock_data(df)
            
            # Calculate metrics
            df['moving_avg_7'] = StockAnalytics.calculate_moving_average(
                df, 'close', 7
            )
            df['moving_avg_30'] = StockAnalytics.calculate_moving_average(
                df, 'close', 30
            )
            df['volatility'] = StockAnalytics.calculate_volatility(
                df, 'close', 30
            )
            df = StockAnalytics.calculate_price_change(df)
            
            # Add trend
            df['trend'] = StockAnalytics.identify_trends(df, 7, 30)
            
            self.logger.info(f"✅ Transformed {len(df)} records")
            
            return df
        
        except Exception as e:
            self.logger.error(f"❌ Transform failed: {e}")
            raise
    
    def transform_weather_data(self, df):
        """Transform weather data - add categorizations"""
        
        self.logger.info("🔄 Transforming weather data...")
        
        try:
            # Clean data
            df = DataCleaner.clean_weather_data(df)
            
            # Add categorizations
            df['temp_category'] = df['temperature'].apply(
                WeatherAnalytics.categorize_temperature
            )
            df['humidity_category'] = df['humidity'].apply(
                WeatherAnalytics.categorize_humidity
            )
            
            # Add stress index
            df['weather_stress_index'] = df.apply(
                lambda row: WeatherAnalytics.weather_stress_index(
                    row['temperature'],
                    row['humidity'],
                    row['wind_speed']
                ),
                axis=1
            )
            
            self.logger.info(f"✅ Transformed {len(df)} records")
            
            return df
        
        except Exception as e:
            self.logger.error(f"❌ Transform failed: {e}")
            raise
    
    def load_stock_analytics(self, df):
        """Load calculated stock metrics to database"""
        
        self.logger.info("📥 Loading stock analytics...")
        
        try:
            # Prepare data for insertion
            load_df = df[[
                'symbol', 'date', 'price_change', 'price_change_percent',
                'moving_avg_7', 'moving_avg_30', 'volatility'
            ]].copy()
            
            # Insert
            self.db.insert_dataframe(load_df, 'stock_analytics')
            
            self.logger.info(f"✅ Loaded {len(load_df)} records")
        
        except Exception as e:
            self.logger.error(f"❌ Load failed: {e}")
            raise
    
    def analyze_correlations(self, symbol, city):
        """
        Find correlation between weather and stock prices
        
        Args:
            symbol: Stock symbol
            city: City name
        """
        
        self.logger.info(f"\n📊 Analyzing correlation: {symbol} vs {city} weather")
        
        try:
            # Extract data
            stock_df = self.extract_stock_data(symbol)
            weather_df = self.extract_weather_data(city)
            
            if len(stock_df) == 0 or len(weather_df) == 0:
                self.logger.warning("⚠️ Insufficient data for correlation")
                return None
            
            # Transform
            stock_df = self.transform_stock_data(stock_df)
            weather_df = self.transform_weather_data(weather_df)
            
            # Analyze correlation
            correlation_result = CorrelationAnalysis.calculate_correlation(
                stock_df,
                weather_df,
                city
            )
            
            if correlation_result:
                # Display findings
                self.logger.info("\n📈 Correlation Findings:")
                for finding in correlation_result['interpretation']:
                    self.logger.info(f"   • {finding}")
                
                # Save to database
                self.save_correlation_result(correlation_result)
            
            return correlation_result
        
        except Exception as e:
            self.logger.error(f"❌ Correlation analysis failed: {e}")
            raise
    
    # def save_correlation_result(self, result):
    #     """Save correlation analysis to database"""
        
    #     findings_text = '\n'.join(result['interpretation'])
        
    #     query = """
    #         INSERT INTO correlation_analysis 
    #         (symbol, city, analysis_date, correlation_coefficient, 
    #          sample_size, analysis_type, findings)
    #         VALUES (%s, %s, %s, %s, %s, %s, %s)
    #         ON CONFLICT DO NOTHING
    #     """
        
    #     try:
    #         with self.db.cursor() as cur:
    #             cur.execute(query, (
    #                 result['symbol'],
    #                 result['city'],
    #                 datetime.now().date(),
    #                 str(result['correlations']),  # Store as string
    #                 result['sample_size'],
    #                 'weather_stock_correlation',
    #                 findings_text
    #             ))
            
    #         self.logger.info("✅ Correlation result saved to database")
        
    #     except Exception as e:
    #         self.logger.error(f"❌ Failed to save correlation: {e}")
    
    def save_correlation_result(self, result):
        """Save individual correlation metrics to database."""

        query = """
            INSERT INTO correlation_analysis
            (
                symbol,
                city,
                analysis_date,
                correlation_coefficient,
                sample_size,
                analysis_type,
                findings
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (symbol, city, analysis_date, analysis_type)
            DO UPDATE SET
                correlation_coefficient = EXCLUDED.correlation_coefficient,
                sample_size = EXCLUDED.sample_size,
                findings = EXCLUDED.findings;
        """

        try:
            with self.db.cursor() as cur:

                for metric, coefficient in result['correlations'].items():

                    # Convert NumPy values to normal Python float
                    if pd.isna(coefficient):
                        coefficient = None
                    else:
                        coefficient = float(coefficient)

                    # Find matching interpretation
                    finding = next(
                        (
                            item
                            for item in result['interpretation']
                            if item.startswith(metric + ":")
                        ),
                        metric
                    )

                    cur.execute(
                        query,
                        (
                            result['symbol'],
                            result['city'],
                            datetime.now().date(),
                            coefficient,
                            result['sample_size'],
                            metric,
                            finding
                        )
                    )

            self.logger.info(
                f"✅ Saved {len(result['correlations'])} correlation metrics"
            )

        except Exception as e:
            self.logger.error(
                f"❌ Failed to save correlations: {e}"
            )
            raise

    def run_full_pipeline(self):
        """
        Run complete ETL pipeline
        
        This is the main orchestration method
        """
        
        self.logger.info("=" * 60)
        self.logger.info("STARTING ETL PIPELINE")
        self.logger.info("=" * 60)
        
        try:
            # Configuration
            symbols = ['AAPL', 'GOOGL', 'MSFT']
            cities = ['Mumbai', 'Delhi', 'Bangalore']
            
            # Step 1: Transform stock data for each symbol
            self.logger.info("\n📊 PROCESSING STOCK DATA")
            self.logger.info("-" * 60)
            
            for symbol in symbols:
                try:
                    stock_df = self.extract_stock_data(symbol)
                    
                    if len(stock_df) > 0:
                        stock_df = self.transform_stock_data(stock_df)
                        self.load_stock_analytics(stock_df)
                    else:
                        self.logger.warning(f"No data for {symbol}")
                
                except Exception as e:
                    self.logger.error(f"Failed to process {symbol}: {e}")
                    continue
            
            # Step 2: Transform weather data
            self.logger.info("\n🌤️ PROCESSING WEATHER DATA")
            self.logger.info("-" * 60)
            
            for city in cities:
                try:
                    weather_df = self.extract_weather_data(city)
                    
                    if len(weather_df) > 0:
                        weather_df = self.transform_weather_data(weather_df)
                    else:
                        self.logger.warning(f"No data for {city}")
                
                except Exception as e:
                    self.logger.error(f"Failed to process {city}: {e}")
                    continue
            
            # Step 3: Correlation analysis
            self.logger.info("\n📈 CORRELATION ANALYSIS")
            self.logger.info("-" * 60)
            
            for symbol in symbols:
                for city in cities:
                    try:
                        self.analyze_correlations(symbol, city)
                    except Exception as e:
                        self.logger.error(
                            f"Correlation failed for {symbol}-{city}: {e}"
                        )
                        continue
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info("✅ ETL PIPELINE COMPLETED SUCCESSFULLY")
            self.logger.info("=" * 60)
        
        except Exception as e:
            self.logger.error(f"❌ PIPELINE FAILED: {e}")
            raise


# ============== MAIN EXECUTION ==============

if __name__ == "__main__":
    
    # Get RDS credentials
    RDS_HOST = os.getenv('RDS_HOST')
    RDS_USER = os.getenv('RDS_USER')
    RDS_PASSWORD = os.getenv('RDS_PASSWORD')
    
    # Connect to database
    db = DatabaseConnection(
        host=RDS_HOST,
        user=RDS_USER,
        password=RDS_PASSWORD,
        database='stock_weather_db'
    )
    db.connect()
    
    # Run pipeline
    pipeline = ETLPipeline(db)
    pipeline.run_full_pipeline()
    
    # Disconnect
    db.disconnect()