import getpass
import os

import dotenv
from psycopg2 import pool

dotenv.load_dotenv()

DB_URL = os.getenv("DATABASE_URL")

DB_CREDENTIALS = {
    "dbname": "class_api",
    "user": getpass.getuser(),
    "password": "",
    "host": "localhost",
    "port": "5432",
}

CONNECT_KWARGS = {
    "connect_timeout": 10,
    "keepalives": 1,
    "keepalives_idle": 30,
    "keepalives_interval": 10,
    "keepalives_count": 5,
}


def get_db_connect_params():
    """Return psycopg2 connection params for Supabase (preferred) or local Postgres."""
    if DB_URL:
        return {
            "dsn": DB_URL,
            "sslmode": "require",
            **CONNECT_KWARGS,
        }

    return {
        **DB_CREDENTIALS,
        **CONNECT_KWARGS,
    }


def create_threaded_connection_pool(minconn=1, maxconn=20):
    """Create a ThreadedConnectionPool using shared DB config."""
    return pool.ThreadedConnectionPool(minconn, maxconn, **get_db_connect_params())
