import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta


class StockAnalytics:
    """Calculate stock analytics metrics"""

    @staticmethod
    def calculate_moving_average(df, column='close', window=7):
        """
        Calculate moving average

        Args:
            df: DataFrame with stock data
            column: Column to calculate MA on
            window: Window size (7 or 30 days)

        Returns:
            Series with moving average
        """
        return df[column].rolling(
            window=window,
            min_periods=1
        ).mean()

    @staticmethod
    def calculate_volatility(df, column='close', window=30):
        """
        Calculate price volatility (standard deviation)

        High volatility = price jumps around
        Low volatility = stable price
        """
        returns = df[column].pct_change()
        volatility = returns.rolling(
            window=window
        ).std() * 100

        return volatility

    @staticmethod
    def calculate_price_change(df):
        """Calculate daily price change and percent change"""
        df['price_change'] = df['close'].diff()
        df['price_change_percent'] = df['close'].pct_change() * 100

        return df

    @staticmethod
    def identify_trends(df, short_window=7, long_window=30):
        """
        Identify uptrend/downtrend

        Returns:
            'UPTREND' if short MA > long MA
            'DOWNTREND' if short MA < long MA
        """
        short_ma = df['close'].rolling(
            window=short_window
        ).mean()

        long_ma = df['close'].rolling(
            window=long_window
        ).mean()

        trend = np.where(
            short_ma > long_ma,
            'UPTREND',
            'DOWNTREND'
        )

        return trend


class WeatherAnalytics:
    """Analyze weather patterns"""

    @staticmethod
    def categorize_temperature(temp):
        """Categorize temperature"""

        if temp < 10:
            return 'COLD'
        elif temp < 20:
            return 'COOL'
        elif temp < 30:
            return 'WARM'
        else:
            return 'HOT'

    @staticmethod
    def categorize_humidity(humidity):
        """Categorize humidity level"""

        if humidity < 30:
            return 'DRY'
        elif humidity < 60:
            return 'MODERATE'
        else:
            return 'HUMID'

    @staticmethod
    def weather_stress_index(temp, humidity, wind):
        """
        Create composite weather stress index
        Scale: 0-100 (higher = more extreme)

        Used to see if extreme weather affects stocks
        """

        # Normalize each component (0-100)
        temp_stress = float(abs(temp - 20)) * 2.5
        humidity_stress = float(abs(humidity - 50))
        wind_stress = float(wind) * 10

        # Composite
        stress = (
            temp_stress +
            humidity_stress +
            wind_stress
        ) / 3

        return min(stress, 100)


class DataCleaner:
    """Clean and validate data"""

    @staticmethod
    def clean_stock_data(df):
        """Clean stock price data"""

        print("🧹 Cleaning stock data...")

        # Remove rows with missing prices
        df = df.dropna(
            subset=['close', 'volume']
        )

        # Remove rows with invalid prices
        df = df[df['close'] > 0]
        df = df[df['volume'] > 0]

        # Remove duplicates
        df = df.drop_duplicates(
            subset=['date']
        )

        # Sort by date
        df = df.sort_values('date')

        print(f"✅ Cleaned {len(df)} records")

        return df

    @staticmethod
    def clean_weather_data(df):
        """Clean weather data"""

        print("🧹 Cleaning weather data...")

        # Remove rows with missing temperatures
        df = df.dropna(
            subset=['temperature', 'humidity']
        )

        # Remove duplicates by city and date
        df = df.drop_duplicates(
            subset=['city', 'recorded_date']
        )

        # Sort by date
        df = df.sort_values('recorded_date')

        print(f"✅ Cleaned {len(df)} records")

        return df

    @staticmethod
    def handle_missing_values(df, strategy='interpolate'):
        """
        Handle missing values

        Args:
            df: DataFrame
            strategy: 'interpolate' (fill based on trend)
                      'forward_fill' (use previous value)
                      'drop' (remove rows)
        """

        if strategy == 'interpolate':
            return df.interpolate(
                method='linear',
                limit_direction='both'
            )

        elif strategy == 'forward_fill':
            return df.fillna(
                method='ffill'
            ).fillna(method='bfill')

        elif strategy == 'drop':
            return df.dropna()

        return df


class CorrelationAnalysis:
    """Find relationships between weather and stocks"""

    @staticmethod
    def calculate_correlation(
        stock_prices,
        weather_data,
        city='Mumbai'
    ):
        """
        Calculate correlation between weather and stock prices

        Args:
            stock_prices: DataFrame with stock prices
            weather_data: DataFrame with weather data
            city: Target city

        Returns:
            dict: Correlation metrics
        """

        print(
            f"\n📊 Analyzing correlation: "
            f"{city} weather vs stocks..."
        )

        # Filter data for specific city
        city_weather = weather_data[
            weather_data['city'] == city
        ].copy()

        # Merge weather and stock data by date
        city_weather['date'] = (
            city_weather['recorded_date']
        )

        stock_prices['date'] = pd.to_datetime(
            stock_prices['date']
        ).dt.date

        merged = stock_prices.merge(
            city_weather,
            on='date',
            how='inner'
        )

        if len(merged) < 5:
            print(
                "⚠️ Not enough data points "
                "for correlation"
            )
            return None

        print(
            f"📈 Sample size: {len(merged)} days"
        )

        # Calculate Pearson correlation
        correlations = {
            'temp_vs_close': stats.pearsonr(
                merged['temperature'],
                merged['close']
            )[0],

            'humidity_vs_volume': stats.pearsonr(
                merged['humidity'],
                merged['volume']
            )[0],

            'wind_vs_volatility': stats.pearsonr(
                merged['wind_speed'],
                merged['close'].pct_change()
            )[0]
        }

        return {
            'city': city,
            'symbol': stock_prices['symbol'].iloc[0],
            'sample_size': len(merged),
            'correlations': correlations,
            'interpretation':
                CorrelationAnalysis.interpret_correlation(
                    correlations
                )
        }

    @staticmethod
    def interpret_correlation(correlations):
        """
        Interpret correlation values

        -1 to 1 scale:
        -1: Perfect negative
        0: No relationship
        1: Perfect positive
        """

        findings = []

        for metric, value in correlations.items():

            if value > 0.5:
                strength = "Strong positive"

            elif value > 0.2:
                strength = "Weak positive"

            elif value < -0.5:
                strength = "Strong negative"

            elif value < -0.2:
                strength = "Weak negative"

            else:
                strength = "No relationship"

            findings.append(
                f"{metric}: {strength} ({value:.3f})"
            )

        return findings


# ============== EXAMPLE USAGE ==============

if __name__ == "__main__":

    # Load sample data
    stock_df = pd.read_csv(
        'data_ingestion/raw_data/AAPL_daily.csv'
    )

    # Clean
    stock_df = DataCleaner.clean_stock_data(
        stock_df
    )

    # Calculate metrics
    stock_df['moving_avg_7'] = (
        StockAnalytics.calculate_moving_average(
            stock_df,
            window=7
        )
    )

    stock_df['moving_avg_30'] = (
        StockAnalytics.calculate_moving_average(
            stock_df,
            window=30
        )
    )

    stock_df['volatility'] = (
        StockAnalytics.calculate_volatility(
            stock_df,
            window=30
        )
    )

    stock_df = StockAnalytics.calculate_price_change(
        stock_df
    )

    # Display results
    print("\n📊 Sample Analytics:")

    print(
        stock_df[
            [
                'date',
                'close',
                'moving_avg_7',
                'moving_avg_30',
                'volatility'
            ]
        ].tail()
    )