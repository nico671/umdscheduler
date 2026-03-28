import sys
from contextlib import contextmanager
from pathlib import Path

import psycopg2.extras

try:
    from common.db_config import create_threaded_connection_pool
except ModuleNotFoundError:
    backend_root = Path(__file__).resolve().parents[1]
    if str(backend_root) not in sys.path:
        sys.path.append(str(backend_root))
    from common.db_config import create_threaded_connection_pool


# Initialize the pool (min 1 connection, max 20 connections)
db_pool = create_threaded_connection_pool(1, 20)


# 2. Dependency Generator: Safely checks out and returns connections
@contextmanager
def get_db_connection():
    conn = db_pool.getconn()
    try:
        # Return the connection as a dictionary, making it much easier to convert to JSON
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cursor
    finally:
        cursor.close()
        db_pool.putconn(conn)
