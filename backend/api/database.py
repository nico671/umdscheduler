import getpass
from contextlib import contextmanager

from psycopg2 import pool

# 1. Initialize the pool (min 1 connection, max 20 connections)
db_pool = pool.ThreadedConnectionPool(
    1,
    20,
    dbname="class_api",
    user=getpass.getuser(),
    password="",
    host="localhost",
    port="5432",
)


# 2. Dependency Generator: Safely checks out and returns connections
@contextmanager
def get_db_connection():
    conn = db_pool.getconn()
    try:
        # Return the connection as a dictionary, making it much easier to convert to JSON
        import psycopg2.extras

        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        yield cursor
    finally:
        cursor.close()
        db_pool.putconn(conn)
