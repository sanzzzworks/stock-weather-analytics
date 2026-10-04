import requests
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

START_DATE = "2026-04-28"
END_DATE = "2026-09-18"

OUTPUT_DIR = "data_ingestion/raw_data"

CITIES = {
    "Mumbai": {
        "latitude": 19.0760,
        "longitude": 72.8777
    },
    "Delhi": {
        "latitude": 28.6139,
        "longitude": 77.2090
    },
    "Bangalore": {
        "latitude": 12.9716,
        "longitude": 77.5946
    }
}


# ============================================================
# FETCH HISTORICAL WEATHER
# ============================================================

def fetch_historical_weather(city, latitude, longitude):
    """
    Fetch daily historical weather data from Open-Meteo.
    """

    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": START_DATE,
        "end_date": END_DATE,

        "daily": ",".join([
            "temperature_2m_mean",
            "apparent_temperature_mean",
            "relative_humidity_2m_mean",
            "surface_pressure_mean",
            "wind_speed_10m_max",
            "cloud_cover_mean",
            "precipitation_sum",
            "weather_code"
        ]),

        "temperature_unit": "celsius",

        # Use m/s to stay consistent with the existing
        # OpenWeather-style wind_speed field.
        "wind_speed_unit": "ms",

        "timezone": "Asia/Kolkata"
    }

    print()
    print("=" * 60)
    print(f"Fetching weather: {city}")
    print("=" * 60)

    response = requests.get(url, params=params, timeout=30)

    response.raise_for_status()

    data = response.json()

    if "daily" not in data:
        raise ValueError(f"No daily weather data returned for {city}")

    daily = data["daily"]

    df = pd.DataFrame({
        "recorded_date": daily["time"],
        "temperature": daily["temperature_2m_mean"],
        "feels_like": daily["apparent_temperature_mean"],
        "humidity": daily["relative_humidity_2m_mean"],
        "pressure": daily["surface_pressure_mean"],
        "wind_speed": daily["wind_speed_10m_max"],
        "cloudiness": daily["cloud_cover_mean"],
        "precipitation": daily["precipitation_sum"],
        "weather_code": daily["weather_code"]
    })

    df["city"] = city

    # Reorder columns
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
            "precipitation",
            "weather_code"
        ]
    ]

    return df


# ============================================================
# MAIN
# ============================================================

def main():

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    all_data = []

    for city, coordinates in CITIES.items():

        try:

            df = fetch_historical_weather(
                city,
                coordinates["latitude"],
                coordinates["longitude"]
            )

            print(f"Records received: {len(df)}")

            print(
                f"Date range: "
                f"{df['recorded_date'].min()} → "
                f"{df['recorded_date'].max()}"
            )

            all_data.append(df)

        except Exception as e:

            print(f"ERROR fetching {city}: {e}")

    if not all_data:
        raise RuntimeError("No weather data was downloaded.")

    final_df = pd.concat(
        all_data,
        ignore_index=True
    )

    # Remove duplicate city/date combinations
    final_df = final_df.drop_duplicates(
        subset=["city", "recorded_date"]
    )

    # Save combined file
    output_file = os.path.join(
        OUTPUT_DIR,
        "historical_weather.csv"
    )

    final_df.to_csv(
        output_file,
        index=False
    )

    print()
    print("=" * 60)
    print("HISTORICAL WEATHER DOWNLOAD COMPLETE")
    print("=" * 60)

    print(f"Total records: {len(final_df)}")

    print()
    print("Records by city:")

    print(
        final_df.groupby("city")
        .size()
    )

    print()
    print(f"Saved to: {output_file}")


if __name__ == "__main__":
    main()