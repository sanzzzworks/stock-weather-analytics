# data_ingestion/fetch_market_data.py
import requests
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
import time
import json

# Load environment variables
load_dotenv()

ALPHA_VANTAGE_KEY = os.getenv('ALPHA_VANTAGE_API_KEY')
WEATHER_KEY = os.getenv('OPENWEATHERMAP_API_KEY')

class StockDataFetcher:
    """Fetch stock market data from Alpha Vantage API"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.data_dir = "data_ingestion/raw_data"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def fetch_daily_prices(self, symbol, output_size='compact'):
        """
        Fetch daily stock prices for given symbol
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL', 'GOOGL')
            output_size (str): 'compact' (100 days) or 'full' (20 years)
        
        Returns:
            pd.DataFrame: Stock data with timestamps
        """
        params = {
            'function': 'TIME_SERIES_DAILY',
            'symbol': symbol,
            'apikey': self.api_key,
            'outputsize': output_size
        }
        
        print(f"📊 Fetching stock data for {symbol}...")
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()  # Raise error if status code is bad
            
            data = response.json()
            
            # Check for API errors
            if 'Error Message' in data:
                print(f"❌ Error: {data['Error Message']}")
                return None
            
            if 'Time Series (Daily)' not in data:
                print(f"⚠️ Warning: No data returned. Check API limit or symbol.")
                return None
            
            # Convert to DataFrame
            time_series = data['Time Series (Daily)']
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index.name = 'timestamp'
            df.index = pd.to_datetime(df.index)
            
            # Rename columns
            df.columns = ['open', 'high', 'low', 'close', 'volume']
            
            # Convert to numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Sort by date (oldest first)
            df = df.sort_index()
            
            # Add metadata
            df['symbol'] = symbol
            df['fetch_timestamp'] = datetime.now()
            
            print(f"✅ Successfully fetched {len(df)} records for {symbol}")
            
            return df
        
        except requests.exceptions.RequestException as e:
            print(f"❌ API Request failed: {e}")
            return None
    
    def save_to_csv(self, df, symbol):
        """Save data to CSV"""
        filepath = f"{self.data_dir}/{symbol}_daily.csv"
        df.to_csv(filepath)
        print(f"💾 Saved to {filepath}")
        return filepath


class WeatherDataFetcher:
    """Fetch weather data from OpenWeatherMap API"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5/weather"
        self.data_dir = "data_ingestion/raw_data"
        os.makedirs(self.data_dir, exist_ok=True)
    
    def fetch_weather(self, city, country_code='IN'):
        """
        Fetch current weather for a city
        
        Args:
            city (str): City name (e.g., 'Mumbai')
            country_code (str): ISO 3166 country code
        
        Returns:
            dict: Weather data
        """
        params = {
            'q': f"{city},{country_code}",
            'appid': self.api_key,
            'units': 'metric'  # Celsius
        }
        
        print(f"🌤️ Fetching weather for {city}...")
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract relevant fields
            weather_data = {
                'timestamp': datetime.now(),
                'city': city,
                'temperature': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'humidity': data['main']['humidity'],
                'pressure': data['main']['pressure'],
                'wind_speed': data['wind']['speed'],
                'cloudiness': data['clouds']['all'],
                'description': data['weather'][0]['description']
            }
            
            print(f"✅ Weather data fetched: {weather_data['temperature']}°C")
            return weather_data
        
        except requests.exceptions.RequestException as e:
            print(f"❌ Weather API failed: {e}")
            return None
    
    def save_weather_log(self, weather_data):
        """Append weather data to log file"""
        filepath = f"{self.data_dir}/weather_log.json"
        
        # Read existing data or start new
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                data_list = json.load(f)
        else:
            data_list = []
        
        # Append new record
        data_list.append(weather_data)
        
        # Save
        with open(filepath, 'w') as f:
            json.dump(data_list, f, indent=2, default=str)
        
        print(f"💾 Weather data saved to {filepath}")


# ============== MAIN EXECUTION ==============

if __name__ == "__main__":
    
    # Example 1: Fetch stock data
    stock_fetcher = StockDataFetcher(ALPHA_VANTAGE_KEY)
    
    # Stock symbols to monitor
    symbols = ['AAPL', 'GOOGL', 'MSFT']
    
    for symbol in symbols:
        df = stock_fetcher.fetch_daily_prices(symbol)
        if df is not None:
            stock_fetcher.save_to_csv(df, symbol)
        
        # Important: Wait 5 seconds between requests to avoid API limit
        print("⏳ Waiting 5 seconds before next request...")
        time.sleep(5)
    
    # Example 2: Fetch weather data
    weather_fetcher = WeatherDataFetcher(WEATHER_KEY)
    
    cities = ['Mumbai', 'Delhi', 'Bangalore']
    
    for city in cities:
        weather = weather_fetcher.fetch_weather(city)
        if weather:
            weather_fetcher.save_weather_log(weather)
        time.sleep(2)  # Rate limiting
    
    print("\n✅ Data ingestion complete!")
    print("📁 Check 'data_ingestion/raw_data' folder for CSV files")