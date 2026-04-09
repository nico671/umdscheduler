import getpass

from psycopg2 import pool

from common.settings import get_settings

DB_CREDENTIALS = {
    "dbname": "class_api",
    "user": getpass.getuser(),
    "password": "",
    "host": "localhost",
    "port": "5432",
}


def get_db_connect_params():
    """Return psycopg2 connection params for Supabase (preferred) or local Postgres."""
    settings = get_settings()
    connect_kwargs = {
        "connect_timeout": settings.db_connect_timeout,
        "keepalives": settings.db_keepalives,
        "keepalives_idle": settings.db_keepalives_idle,
        "keepalives_interval": settings.db_keepalives_interval,
        "keepalives_count": settings.db_keepalives_count,
    }

    if settings.database_url:
        return {
            "dsn": settings.database_url,
            "sslmode": settings.db_ssl_mode,
            **connect_kwargs,
        }

    return {
        **DB_CREDENTIALS,
        **connect_kwargs,
    }


def create_threaded_connection_pool(minconn=None, maxconn=None):
    """Create a ThreadedConnectionPool using shared DB config."""
    settings = get_settings()
    resolved_minconn = settings.db_pool_min if minconn is None else minconn
    resolved_maxconn = settings.db_pool_max if maxconn is None else maxconn
    return pool.ThreadedConnectionPool(
        resolved_minconn,
        resolved_maxconn,
        **get_db_connect_params(),
    )
