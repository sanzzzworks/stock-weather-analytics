import os
import pandas as pd
from dotenv import load_dotenv
from psycopg2.extras import execute_values

from db_connection import DatabaseConnection, init_database

load_dotenv()


def load_historical_weather(db):

    weather_file = os.path.join(
        "data_ingestion",
        "raw_data",
        "historical_weather.csv"
    )

    print(f"\nLoading historical weather file: {weather_file}")

    # Read CSV
    df = pd.read_csv(weather_file)

    print(f"CSV records: {len(df)}")

    # Convert date
    df["recorded_date"] = pd.to_datetime(
        df["recorded_date"]
    ).dt.date

    # Existing weather_data table does not contain
    # precipitation or weather_code columns.
    df["description"] = None

    # Keep only columns that exist in PostgreSQL
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

    # Remove duplicate city/date combinations
    df = df.drop_duplicates(
        subset=["city", "recorded_date"]
    )

    print(f"Records after cleaning: {len(df)}")

    # Display city counts
    print("\nRecords by city:")
    print(df["city"].value_counts())

    print("\nDate ranges:")

    for city in sorted(df["city"].unique()):
        city_df = df[df["city"] == city]

        print(
            f"{city}: "
            f"{city_df['recorded_date'].min()} "
            f"to "
            f"{city_df['recorded_date'].max()}"
        )

    # --------------------------------------------------
    # Clear existing weather data
    # --------------------------------------------------

    print("\nClearing existing weather_data...")

    with db.cursor() as cur:
        cur.execute("DELETE FROM weather_data;")

    print("Old weather records removed.")

    # --------------------------------------------------
    # Batch insert
    # --------------------------------------------------

    print("\nInserting historical weather data...")

    insert_query = """
        INSERT INTO weather_data (
            city,
            recorded_date,
            temperature,
            feels_like,
            humidity,
            pressure,
            wind_speed,
            cloudiness,
            description
        )
        VALUES %s
        ON CONFLICT (city, recorded_date)
        DO NOTHING;
    """

    records = [
        tuple(row)
        for row in df.itertuples(index=False, name=None)
    ]

    batch_size = 50

    total_inserted = 0

    for start in range(0, len(records), batch_size):

        batch = records[start:start + batch_size]

        print(
            f"Inserting rows "
            f"{start + 1}-{start + len(batch)}..."
        )

        with db.cursor() as cur:

            execute_values(
                cur,
                insert_query,
                batch,
                page_size=batch_size
            )

        total_inserted += len(batch)

    print(
        f"\nInserted approximately "
        f"{total_inserted} records."
    )


def verify_data(db):

    print("\n--- Data Verification ---")

    result = db.query("""
        SELECT COUNT(*) AS count
        FROM weather_data;
    """)

    print(
        f"Weather records: "
        f"{result[0]['count']}"
    )

    print("\nRecords by city:")

    city_counts = db.query("""
        SELECT
            city,
            COUNT(*) AS count,
            MIN(recorded_date) AS start_date,
            MAX(recorded_date) AS end_date
        FROM weather_data
        GROUP BY city
        ORDER BY city;
    """)

    for row in city_counts:
        print(
            f"{row['city']}: "
            f"{row['count']} records | "
            f"{row['start_date']} → "
            f"{row['end_date']}"
        )

    print("\nChecking duplicates...")

    duplicates = db.query("""
        SELECT
            city,
            recorded_date,
            COUNT(*) AS count
        FROM weather_data
        GROUP BY city, recorded_date
        HAVING COUNT(*) > 1;
    """)

    if duplicates:
        print("WARNING: Duplicate records found!")

        for row in duplicates:
            print(row)
    else:
        print("No duplicate city/date records found.")


def main():

    print("Initializing database...")

    db = init_database()

    try:

        load_historical_weather(db)

        verify_data(db)

    finally:

        db.disconnect()

    print(
        "\nHistorical weather loading "
        "completed successfully!"
    )


if __name__ == "__main__":
    main()