"""
Stock-Weather Analytics
HTML Dashboard Generator

Generates a standalone HTML dashboard using:
- PostgreSQL RDS
- Plotly
- Current project database schema

Database tables used:
    stock_prices
    stock_analytics
    weather_data
    correlation_analysis
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import os
import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from dotenv import load_dotenv

from data_storage.db_connection import DatabaseConnection


# ============================================================
# CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_FILE = PROJECT_ROOT / "dashboards" / "index.html"

load_dotenv(PROJECT_ROOT / ".env")


# ============================================================
# DATABASE CONNECTION
# ============================================================

def create_database_connection():
    """Create PostgreSQL database connection."""

    db = DatabaseConnection(
        host=os.getenv("RDS_HOST"),
        user=os.getenv("RDS_USER"),
        password=os.getenv("RDS_PASSWORD"),
        database="stock_weather_db"
    )

    db.connect()
    return db


# ============================================================
# DATA LOADING
# ============================================================

def load_stock_prices(db):
    """Load stock price data."""

    query = """
        SELECT
            date,
            symbol,
            open,
            high,
            low,
            close,
            volume
        FROM stock_prices
        ORDER BY date, symbol;
    """

    rows = db.query(query)

    return pd.DataFrame(rows)


def load_stock_analytics(db):
    """Load calculated stock analytics."""

    query = """
        SELECT
            date,
            symbol,
            price_change,
            price_change_percent,
            moving_avg_7,
            moving_avg_30,
            volatility
        FROM stock_analytics
        ORDER BY date, symbol;
    """

    rows = db.query(query)

    return pd.DataFrame(rows)


def load_weather_data(db):
    """Load historical weather data."""

    query = """
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
        ORDER BY recorded_date, city;
    """

    rows = db.query(query)

    return pd.DataFrame(rows)


def load_correlations(db):
    """Load weather-stock correlation results."""

    query = """
        SELECT
            symbol,
            city,
            analysis_date,
            analysis_type,
            correlation_coefficient,
            sample_size,
            findings
        FROM correlation_analysis
        ORDER BY symbol, city, analysis_type;
    """

    rows = db.query(query)

    return pd.DataFrame(rows)


# ============================================================
# DATA PREPARATION
# ============================================================

def prepare_data(stock_prices, stock_analytics, weather, correlations):
    """Convert dates and numeric columns to appropriate types."""

    if not stock_prices.empty:
        stock_prices["date"] = pd.to_datetime(stock_prices["date"])

    if not stock_analytics.empty:
        stock_analytics["date"] = pd.to_datetime(
            stock_analytics["date"]
        )

    if not weather.empty:
        weather["recorded_date"] = pd.to_datetime(
            weather["recorded_date"]
        )

    if not correlations.empty:
        correlations["analysis_date"] = pd.to_datetime(
            correlations["analysis_date"]
        )

    return (
        stock_prices,
        stock_analytics,
        weather,
        correlations
    )


# ============================================================
# DASHBOARD METRICS
# ============================================================

def calculate_summary_metrics(
    stock_prices,
    stock_analytics,
    weather,
    correlations
):
    """Calculate headline dashboard metrics."""

    metrics = {}

    metrics["stock_records"] = len(stock_prices)
    metrics["weather_records"] = len(weather)
    metrics["correlation_records"] = len(correlations)

    metrics["symbols"] = (
        sorted(stock_prices["symbol"].dropna().unique().tolist())
        if not stock_prices.empty
        else []
    )

    metrics["cities"] = (
        sorted(weather["city"].dropna().unique().tolist())
        if not weather.empty
        else []
    )

    if not stock_prices.empty:
        latest_date = stock_prices["date"].max()

        latest_prices = stock_prices[
            stock_prices["date"] == latest_date
        ]

        metrics["latest_date"] = latest_date.strftime("%Y-%m-%d")

        metrics["latest_prices"] = {
            row["symbol"]: float(row["close"])
            for _, row in latest_prices.iterrows()
        }

    else:
        metrics["latest_date"] = "N/A"
        metrics["latest_prices"] = {}

    return metrics


# ============================================================
# CHART 1 — STOCK PRICE + MOVING AVERAGES
# ============================================================

def create_stock_price_chart(
    stock_prices,
    stock_analytics
):
    """Create stock price and moving-average chart."""

    fig = go.Figure()

    for symbol in sorted(stock_prices["symbol"].unique()):

        prices = stock_prices[
            stock_prices["symbol"] == symbol
        ].copy()

        analytics = stock_analytics[
            stock_analytics["symbol"] == symbol
        ].copy()

        fig.add_trace(
            go.Scatter(
                x=prices["date"],
                y=prices["close"],
                mode="lines",
                name=f"{symbol} Close",
                visible=True
            )
        )

        fig.add_trace(
            go.Scatter(
                x=analytics["date"],
                y=analytics["moving_avg_7"],
                mode="lines",
                name=f"{symbol} MA 7",
                visible=True
            )
        )

        fig.add_trace(
            go.Scatter(
                x=analytics["date"],
                y=analytics["moving_avg_30"],
                mode="lines",
                name=f"{symbol} MA 30",
                visible=True
            )
        )

    fig.update_layout(
        title="Stock Price & Moving Averages",
        xaxis_title="Date",
        yaxis_title="Price",
        hovermode="x unified",
        height=500
    )

    return fig


# ============================================================
# CHART 2 — TRADING VOLUME
# ============================================================

def create_volume_chart(stock_prices):
    """Create trading volume chart."""

    fig = go.Figure()

    for symbol in sorted(stock_prices["symbol"].unique()):

        data = stock_prices[
            stock_prices["symbol"] == symbol
        ]

        fig.add_trace(
            go.Scatter(
                x=data["date"],
                y=data["volume"],
                mode="lines",
                name=symbol
            )
        )

    fig.update_layout(
        title="Trading Volume",
        xaxis_title="Date",
        yaxis_title="Volume",
        hovermode="x unified",
        height=450
    )

    return fig


# ============================================================
# CHART 3 — STOCK VOLATILITY
# ============================================================

def create_volatility_chart(stock_analytics):
    """Create volatility chart."""

    fig = go.Figure()

    for symbol in sorted(
        stock_analytics["symbol"].unique()
    ):

        data = stock_analytics[
            stock_analytics["symbol"] == symbol
        ]

        fig.add_trace(
            go.Scatter(
                x=data["date"],
                y=data["volatility"],
                mode="lines",
                name=symbol
            )
        )

    fig.update_layout(
        title="Stock Volatility",
        xaxis_title="Date",
        yaxis_title="Volatility",
        hovermode="x unified",
        height=450
    )

    return fig


# ============================================================
# CHART 4 — TEMPERATURE
# ============================================================

def create_temperature_chart(weather):
    """Create temperature chart by city."""

    fig = go.Figure()

    for city in sorted(weather["city"].unique()):

        data = weather[
            weather["city"] == city
        ]

        fig.add_trace(
            go.Scatter(
                x=data["recorded_date"],
                y=data["temperature"],
                mode="lines",
                name=city
            )
        )

    fig.update_layout(
        title="Temperature by City",
        xaxis_title="Date",
        yaxis_title="Temperature",
        hovermode="x unified",
        height=450
    )

    return fig


# ============================================================
# CHART 5 — HUMIDITY
# ============================================================

def create_humidity_chart(weather):
    """Create humidity chart by city."""

    fig = go.Figure()

    for city in sorted(weather["city"].unique()):

        data = weather[
            weather["city"] == city
        ]

        fig.add_trace(
            go.Scatter(
                x=data["recorded_date"],
                y=data["humidity"],
                mode="lines",
                name=city
            )
        )

    fig.update_layout(
        title="Humidity by City",
        xaxis_title="Date",
        yaxis_title="Humidity (%)",
        hovermode="x unified",
        height=450
    )

    return fig


# ============================================================
# CHART 6 — WIND SPEED
# ============================================================

def create_wind_chart(weather):
    """Create wind-speed chart by city."""

    fig = go.Figure()

    for city in sorted(weather["city"].unique()):

        data = weather[
            weather["city"] == city
        ]

        fig.add_trace(
            go.Scatter(
                x=data["recorded_date"],
                y=data["wind_speed"],
                mode="lines",
                name=city
            )
        )

    fig.update_layout(
        title="Wind Speed by City",
        xaxis_title="Date",
        yaxis_title="Wind Speed",
        hovermode="x unified",
        height=450
    )

    return fig


# ============================================================
# CHART 7 — CORRELATION
# ============================================================

def create_correlation_chart(correlations):
    """Create weather-stock correlation heatmap."""

    matrix = correlations.pivot_table(
        index="analysis_type",
        columns="symbol",
        values="correlation_coefficient",
        aggfunc="mean"
    )

    fig = go.Figure(
        data=go.Heatmap(
            z=matrix.values,
            x=matrix.columns,
            y=matrix.index,
            text=matrix.round(3).values,
            texttemplate="%{text}",
            colorscale="RdBu",
            zmid=0,
            colorbar_title="Correlation"
        )
    )

    fig.update_layout(
        title="Weather–Stock Correlation Analysis",
        xaxis_title="Stock",
        yaxis_title="Analysis Type",
        height=550
    )

    return fig


# ============================================================
# SUMMARY TABLE
# ============================================================

def create_stock_summary_table(stock_prices):
    """Create stock summary table."""

    summary = (
        stock_prices
        .groupby("symbol")
        .agg(
            Trading_Days=("date", "count"),
            Minimum_Price=("close", "min"),
            Maximum_Price=("close", "max"),
            Average_Price=("close", "mean"),
            Average_Volume=("volume", "mean")
        )
        .reset_index()
    )

    for column in [
        "Minimum_Price",
        "Maximum_Price",
        "Average_Price",
        "Average_Volume"
    ]:
        summary[column] = summary[column].round(2)

    return summary


# ============================================================
# HTML GENERATION
# ============================================================

def generate_html(
    metrics,
    stock_chart,
    volume_chart,
    volatility_chart,
    temperature_chart,
    humidity_chart,
    wind_chart,
    correlation_chart,
    stock_summary
):
    """Generate complete HTML dashboard."""

    stock_chart_html = stock_chart.to_html(
        full_html=False,
        include_plotlyjs=False
    )

    volume_chart_html = volume_chart.to_html(
        full_html=False,
        include_plotlyjs=False
    )

    volatility_chart_html = volatility_chart.to_html(
        full_html=False,
        include_plotlyjs=False
    )

    temperature_chart_html = temperature_chart.to_html(
        full_html=False,
        include_plotlyjs=False
    )

    humidity_chart_html = humidity_chart.to_html(
        full_html=False,
        include_plotlyjs=False
    )

    wind_chart_html = wind_chart.to_html(
        full_html=False,
        include_plotlyjs=False
    )

    correlation_chart_html = correlation_chart.to_html(
        full_html=False,
        include_plotlyjs=False
    )

    summary_html = stock_summary.to_html(
        index=False,
        classes="summary-table",
        border=0
    )

    latest_prices_html = ""

    for symbol, price in metrics["latest_prices"].items():

        latest_prices_html += f"""
        <div class="metric-card">
            <div class="metric-title">{symbol}</div>
            <div class="metric-value">${price:.2f}</div>
        </div>
        """

    html = f"""
<!DOCTYPE html>

<html lang="en">

<head>

    <meta charset="UTF-8">

    <meta
        name="viewport"
        content="width=device-width, initial-scale=1.0"
    >

    <title>Stock-Weather Analytics Dashboard</title>

    <script
        src="https://cdn.plot.ly/plotly-2.35.2.min.js">
    </script>

    <style>

        * {{
            box-sizing: border-box;
        }}

        body {{
            margin: 0;
            font-family:
                Arial,
                Helvetica,
                sans-serif;

            background: #f4f6f8;
            color: #1f2937;
        }}

        .header {{
            background: #111827;
            color: white;
            padding: 28px 40px;
        }}

        .header h1 {{
            margin: 0;
            font-size: 30px;
        }}

        .header p {{
            margin-top: 8px;
            color: #d1d5db;
        }}

        .container {{
            max-width: 1500px;
            margin: auto;
            padding: 25px;
        }}

        .metrics {{
            display: grid;
            grid-template-columns:
                repeat(auto-fit, minmax(180px, 1fr));

            gap: 18px;
            margin-bottom: 25px;
        }}

        .metric-card {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow:
                0 2px 8px rgba(0,0,0,0.08);
        }}

        .metric-title {{
            font-size: 14px;
            color: #6b7280;
            margin-bottom: 8px;
        }}

        .metric-value {{
            font-size: 26px;
            font-weight: bold;
        }}

        .section {{
            background: white;
            border-radius: 10px;
            margin-bottom: 25px;
            padding: 10px;
            box-shadow:
                0 2px 8px rgba(0,0,0,0.08);
        }}

        .section h2 {{
            padding: 10px 20px;
            margin-bottom: 0;
            font-size: 21px;
        }}

        .chart {{
            width: 100%;
        }}

        .table-container {{
            overflow-x: auto;
            padding: 20px;
        }}

        .summary-table {{
            width: 100%;
            border-collapse: collapse;
        }}

        .summary-table th,
        .summary-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }}

        .summary-table th {{
            background: #f3f4f6;
            font-weight: 600;
        }}

        .footer {{
            text-align: center;
            color: #6b7280;
            padding: 30px;
            font-size: 14px;
        }}

        @media (max-width: 700px) {{

            .header {{
                padding: 20px;
            }}

            .container {{
                padding: 12px;
            }}

            .header h1 {{
                font-size: 24px;
            }}

        }}

    </style>

</head>


<body>

    <div class="header">

        <h1>
            Stock-Weather Analytics Dashboard
        </h1>

        <p>
            Market performance, weather patterns,
            volatility and correlation analysis
        </p>

    </div>


    <div class="container">


        <!-- ================================================= -->
        <!-- SUMMARY METRICS -->
        <!-- ================================================= -->

        <div class="metrics">

            <div class="metric-card">

                <div class="metric-title">
                    Stock Records
                </div>

                <div class="metric-value">
                    {metrics["stock_records"]}
                </div>

            </div>


            <div class="metric-card">

                <div class="metric-title">
                    Weather Records
                </div>

                <div class="metric-value">
                    {metrics["weather_records"]}
                </div>

            </div>


            <div class="metric-card">

                <div class="metric-title">
                    Correlation Records
                </div>

                <div class="metric-value">
                    {metrics["correlation_records"]}
                </div>

            </div>


            <div class="metric-card">

                <div class="metric-title">
                    Latest Data Date
                </div>

                <div class="metric-value">
                    {metrics["latest_date"]}
                </div>

            </div>


            {latest_prices_html}

        </div>


        <!-- ================================================= -->
        <!-- STOCK PRICE -->
        <!-- ================================================= -->

        <div class="section">

            <h2>
                Stock Price & Moving Averages
            </h2>

            <div class="chart">
                {stock_chart_html}
            </div>

        </div>


        <!-- ================================================= -->
        <!-- VOLUME -->
        <!-- ================================================= -->

        <div class="section">

            <h2>
                Trading Volume
            </h2>

            <div class="chart">
                {volume_chart_html}
            </div>

        </div>


        <!-- ================================================= -->
        <!-- VOLATILITY -->
        <!-- ================================================= -->

        <div class="section">

            <h2>
                Stock Volatility
            </h2>

            <div class="chart">
                {volatility_chart_html}
            </div>

        </div>


        <!-- ================================================= -->
        <!-- WEATHER -->
        <!-- ================================================= -->

        <div class="section">

            <h2>
                Temperature by City
            </h2>

            <div class="chart">
                {temperature_chart_html}
            </div>

        </div>


        <div class="section">

            <h2>
                Humidity by City
            </h2>

            <div class="chart">
                {humidity_chart_html}
            </div>

        </div>


        <div class="section">

            <h2>
                Wind Speed by City
            </h2>

            <div class="chart">
                {wind_chart_html}
            </div>

        </div>


        <!-- ================================================= -->
        <!-- CORRELATION -->
        <!-- ================================================= -->

        <div class="section">

            <h2>
                Weather–Stock Correlation Analysis
            </h2>

            <div class="chart">
                {correlation_chart_html}
            </div>

        </div>


        <!-- ================================================= -->
        <!-- STOCK SUMMARY -->
        <!-- ================================================= -->

        <div class="section">

            <h2>
                Stock Summary
            </h2>

            <div class="table-container">

                {summary_html}

            </div>

        </div>


    </div>


    <div class="footer">

        Stock-Weather Analytics |
        PostgreSQL + Python + Plotly

    </div>


</body>

</html>
"""

    return html


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("STOCK-WEATHER ANALYTICS")
    print("HTML DASHBOARD GENERATOR")
    print("=" * 60)

    db = None

    try:

        # ----------------------------------------------------
        # Connect
        # ----------------------------------------------------

        print("\nConnecting to PostgreSQL...")

        db = create_database_connection()

        # ----------------------------------------------------
        # Load data
        # ----------------------------------------------------

        print("Loading stock prices...")

        stock_prices = load_stock_prices(db)

        print(
            f"   Stock records: "
            f"{len(stock_prices)}"
        )

        print("Loading stock analytics...")

        stock_analytics = load_stock_analytics(db)

        print(
            f"   Analytics records: "
            f"{len(stock_analytics)}"
        )

        print("Loading weather data...")

        weather = load_weather_data(db)

        print(
            f"   Weather records: "
            f"{len(weather)}"
        )

        print("Loading correlation data...")

        correlations = load_correlations(db)

        print(
            f"   Correlation records: "
            f"{len(correlations)}"
        )

        # ----------------------------------------------------
        # Validate data
        # ----------------------------------------------------

        if stock_prices.empty:
            raise ValueError(
                "No stock price data found."
            )

        if stock_analytics.empty:
            raise ValueError(
                "No stock analytics data found."
            )

        if weather.empty:
            raise ValueError(
                "No weather data found."
            )

        if correlations.empty:
            raise ValueError(
                "No correlation data found."
            )

        # ----------------------------------------------------
        # Prepare
        # ----------------------------------------------------

        (
            stock_prices,
            stock_analytics,
            weather,
            correlations
        ) = prepare_data(
            stock_prices,
            stock_analytics,
            weather,
            correlations
        )

        # ----------------------------------------------------
        # Metrics
        # ----------------------------------------------------

        print("\nCalculating dashboard metrics...")

        metrics = calculate_summary_metrics(
            stock_prices,
            stock_analytics,
            weather,
            correlations
        )

        # ----------------------------------------------------
        # Charts
        # ----------------------------------------------------

        print("Creating stock price chart...")

        stock_chart = create_stock_price_chart(
            stock_prices,
            stock_analytics
        )

        print("Creating volume chart...")

        volume_chart = create_volume_chart(
            stock_prices
        )

        print("Creating volatility chart...")

        volatility_chart = create_volatility_chart(
            stock_analytics
        )

        print("Creating temperature chart...")

        temperature_chart = create_temperature_chart(
            weather
        )

        print("Creating humidity chart...")

        humidity_chart = create_humidity_chart(
            weather
        )

        print("Creating wind-speed chart...")

        wind_chart = create_wind_chart(
            weather
        )

        print("Creating correlation chart...")

        correlation_chart = create_correlation_chart(
            correlations
        )

        # ----------------------------------------------------
        # Summary table
        # ----------------------------------------------------

        stock_summary = create_stock_summary_table(
            stock_prices
        )

        # ----------------------------------------------------
        # Generate HTML
        # ----------------------------------------------------

        print("\nGenerating HTML dashboard...")

        html = generate_html(
            metrics,
            stock_chart,
            volume_chart,
            volatility_chart,
            temperature_chart,
            humidity_chart,
            wind_chart,
            correlation_chart,
            stock_summary
        )

        OUTPUT_FILE.write_text(
            html,
            encoding="utf-8"
        )

        # ----------------------------------------------------
        # Result
        # ----------------------------------------------------

        print("\n" + "=" * 60)
        print("DASHBOARD GENERATED SUCCESSFULLY")
        print("=" * 60)

        print(
            f"\nOutput file:\n"
            f"{OUTPUT_FILE}"
        )

        print(
            f"\nFile size: "
            f"{OUTPUT_FILE.stat().st_size:,} bytes"
        )

        print(
            "\nOpen the dashboard with:"
        )

        print(
            "  dashboards\\index.html"
        )

    except Exception as error:

        print("\n" + "=" * 60)
        print("DASHBOARD GENERATION FAILED")
        print("=" * 60)

        print(
            f"\nError: {error}"
        )

        raise

    finally:

        if db is not None:

            try:
                db.disconnect()
            except Exception:
                pass


if __name__ == "__main__":
    main()