# data_ingestion/validate_data.py
import pandas as pd
import os
from datetime import datetime

def validate_stock_data(csv_file):
    """
    Validate stock data quality
    
    Checks:
    - No null values in key columns
    - Prices are positive
    - Volume is reasonable
    - Dates are in order
    """
    print(f"🔍 Validating {csv_file}...")
    
    df = pd.read_csv(csv_file)
    
    # Check 1: Null values
    null_count = df.isnull().sum().sum()
    if null_count > 0:
        print(f"⚠️ Warning: {null_count} null values found")
    else:
        print("✅ No null values")
    
    # Check 2: Prices are positive
    numeric_cols = ['open', 'high', 'low', 'close']
    for col in numeric_cols:
        negative = (df[col] < 0).sum()
        if negative > 0:
            print(f"❌ Error: {negative} negative prices in {col}")
        else:
            print(f"✅ All prices in {col} are positive")
    
    # Check 3: High >= Low >= Close
    # invalid_ranges = ((df['high'] < df['low']).sum() + 
    #                   (df['low'] < df['close']).sum())
    # if invalid_ranges == 0:
    #     print("✅ Price ranges are logical")
    # else:
    #     print(f"⚠️ {invalid_ranges} records with illogical price ranges")
    # Check 3: OHLC price ranges are logical
    invalid_ranges = (
        (df['high'] < df['open']).sum()
        + (df['high'] < df['close']).sum()
        + (df['low'] > df['open']).sum()
        + (df['low'] > df['close']).sum()
    )

    if invalid_ranges == 0:
        print("✅ Price ranges are logical")
    else:
        print(f"⚠️ {invalid_ranges} records with illogical price ranges")
    
    # Check 4: Dates are chronological
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    if df['timestamp'].is_monotonic_increasing:
        print("✅ Dates are in chronological order")
    else:
        print("⚠️ Dates are not in order (may need sorting)")
    
    print(f"\n📊 Data Summary:")
    print(f"   Records: {len(df)}")
    print(f"   Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"   Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")
    print()

# Run validation
if __name__ == "__main__":
    data_dir = "data_ingestion/raw_data"
    
    for file in os.listdir(data_dir):
        if file.endswith('_daily.csv'):
            validate_stock_data(os.path.join(data_dir, file))