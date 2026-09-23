import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
from contextlib import contextmanager

load_dotenv()


class DatabaseConnection:
    def __init__(
        self,
        host,
        user,
        password,
        database="postgres",
        port=5432
    ):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.connection = None

    def connect(self):
        """Establish database connection"""
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                port=self.port
            )
            print(f"Connected to database: {self.database}")
            return self.connection

        except Exception as e:
            print(f"Database connection failed: {e}")
            raise

    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            print("Database connection closed")

    @contextmanager
    def cursor(self):
        """Provide database cursor with automatic commit/rollback"""
        cursor = self.connection.cursor(
            cursor_factory=RealDictCursor
        )

        try:
            yield cursor
            self.connection.commit()

        except Exception:
            self.connection.rollback()
            raise

        finally:
            cursor.close()

    def execute_file(self, filepath):
        """Execute SQL commands from a file"""
        with open(filepath, "r") as file:
            sql = file.read()

        with self.cursor() as cursor:
            cursor.execute(sql)

        print(f"Executed SQL file: {filepath}")

    def insert_dataframe(self, df, table_name):
        """Insert DataFrame into database"""
        columns = list(df.columns)
        columns_str = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        query = f"""
            INSERT INTO {table_name} ({columns_str})
            VALUES ({placeholders})
            ON CONFLICT DO NOTHING
        """

        with self.cursor() as cursor:
            for _, row in df.iterrows():
                values = tuple(row)
                cursor.execute(query, values)

        print(f"Inserted {len(df)} rows into {table_name}")

    def query(self, sql, params=None):
        """Execute SELECT query and return results"""
        with self.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()


def init_database():
    """Initialize the stock weather database"""

    host = os.getenv("RDS_HOST")
    user = os.getenv("RDS_USER")
    password = os.getenv("RDS_PASSWORD")
    port = int(os.getenv("RDS_PORT", 5432))

    # Connect to default postgres database
    db = DatabaseConnection(
        host=host,
        user=user,
        password=password,
        database="postgres",
        port=port
    )

    db.connect()

    # # Create application database
    # with db.cursor() as cursor:
    #     cursor.execute(
    #         "CREATE DATABASE stock_weather_db;"
    #     )

    # Create application database if it does not exist
    with db.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = 'stock_weather_db';"
        )

        database_exists = cursor.fetchone()

    if not database_exists:
        db.connection.autocommit = True
        with db.connection.cursor() as cursor:
            cursor.execute(
                "CREATE DATABASE stock_weather_db;"
            )
        db.connection.autocommit = False
        print("Created database: stock_weather_db")
    else:
        print("Database already exists: stock_weather_db")

    db.disconnect()

    # Connect to application database
    db = DatabaseConnection(
        host=host,
        user=user,
        password=password,
        database="stock_weather_db",
        port=port
    )

    db.connect()

    # Execute schema
    schema_path = os.path.join(
        os.path.dirname(__file__),
        "schema.sql"
    )

    db.execute_file(schema_path)

    print("Database initialization completed.")

    return db


if __name__ == "__main__":
    init_database()