import sys
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

import psycopg2.extras

try:
    from common.db_config import create_threaded_connection_pool
except ModuleNotFoundError:
    backend_root = Path(__file__).resolve().parents[1]
    if str(backend_root) not in sys.path:
        sys.path.append(str(backend_root))
    from common.db_config import create_threaded_connection_pool


@lru_cache(maxsize=1)
def get_db_pool():
    return create_threaded_connection_pool()


def _discard_connection(pool, conn):
    pool.putconn(conn, close=True)


@contextmanager
def get_db_connection():
    pool = get_db_pool()
    conn = pool.getconn()
    cursor = None
    returned = False
    operation_error = None

    def discard_connection():
        nonlocal returned
        if returned:
            return
        returned = True
        _discard_connection(pool, conn)

    try:
        try:
            cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            yield cursor
        except BaseException as exc:
            operation_error = exc
            try:
                conn.rollback()
            except BaseException as cleanup_error:
                discard_connection()
                raise exc.with_traceback(exc.__traceback__) from cleanup_error
            raise
        else:
            cursor_to_close = cursor
            cursor = None
            try:
                cursor_to_close.close()
                conn.rollback()
            except BaseException:
                discard_connection()
                raise
    finally:
        if cursor is not None:
            cursor_to_close = cursor
            cursor = None
            try:
                cursor_to_close.close()
            except BaseException as cleanup_error:
                discard_connection()
                if operation_error is not None:
                    raise operation_error.with_traceback(
                        operation_error.__traceback__
                    ) from cleanup_error
                raise

        if not returned:
            try:
                pool.putconn(conn)
                returned = True
            except BaseException as cleanup_error:
                try:
                    discard_connection()
                except BaseException as discard_error:
                    if operation_error is not None:
                        raise operation_error.with_traceback(
                            operation_error.__traceback__
                        ) from discard_error
                    raise discard_error from cleanup_error
                if operation_error is None:
                    raise cleanup_error
