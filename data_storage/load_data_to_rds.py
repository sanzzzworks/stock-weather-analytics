import os
import glob
import json
import pandas as pd
from dotenv import load_dotenv

from db_connection import DatabaseConnection, init_database

load_dotenv()


def load_stock_data(db):
    """Load stock CSV files into stock_prices table"""

    csv_files = glob.glob(
        os.path.join("data_ingestion", "raw_data", "*_daily.csv")
    )

    for file in csv_files:
        print(f"\nLoading stock file: {file}")

        df = pd.read_csv(file)

        # Extract symbol from filename
        symbol = os.path.basename(file).split("_")[0]

        # Rename columns
        df = df.rename(columns={
            "timestamp": "date",
            "1. open": "open",
            "2. high": "high",
            "3. low": "low",
            "4. close": "close",
            "5. volume": "volume"
        })

        # Add symbol
        df["symbol"] = symbol

        # Select required columns
        df = df[
            [
                "symbol",
                "date",
                "open",
                "high",
                "low",
                "close",
                "volume"
            ]
        ]

        # Remove duplicate records
        df = df.drop_duplicates(
            subset=["symbol", "date"]
        )

        db.insert_dataframe(
            df,
            "stock_prices"
        )


def load_weather_data(db):
    """Load weather JSON into weather_data table"""

    weather_file = os.path.join(
        "data_ingestion",
        "raw_data",
        "weather_log.json"
    )

    print(f"\nLoading weather file: {weather_file}")

    with open(weather_file, "r") as file:
        weather_data = json.load(file)

    df = pd.DataFrame(weather_data)

    # Rename columns
    df = df.rename(columns={
        "timestamp": "recorded_date"
    })

    # Convert timestamp to date
    df["recorded_date"] = pd.to_datetime(
        df["recorded_date"]
    ).dt.date

    # Select required columns
    df = df[
        [
            "city",
            "recorded_date",
            "temperature",
            "feels_like",
            "humidity",
            "pressure",
            "wind_speed",
            "cloudiness",
            "description"
        ]
    ]

    # Remove duplicates
    df = df.drop_duplicates(
        subset=["city", "recorded_date"]
    )

    db.insert_dataframe(
        df,
        "weather_data"
    )


def verify_data(db):
    """Verify loaded data"""

    print("\n--- Data Verification ---")

    stock_count = db.query(
        "SELECT COUNT(*) AS count FROM stock_prices;"
    )

    weather_count = db.query(
        "SELECT COUNT(*) AS count FROM weather_data;"
    )

    print(
        f"Stock records: {stock_count[0]['count']}"
    )

    print(
        f"Weather records: {weather_count[0]['count']}"
    )


def main():

    print("Initializing database...")

    db = init_database()

    try:
        load_stock_data(db)
        load_weather_data(db)
        verify_data(db)

    finally:
        db.disconnect()

    print("\nData loading completed successfully!")


if __name__ == "__main__":
    main()