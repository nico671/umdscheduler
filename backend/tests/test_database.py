import unittest
from unittest.mock import patch

from api import database


class FakeCursor:
    def __init__(self, *, close_error=None):
        self.close_error = close_error
        self.closed = False

    def close(self):
        if self.close_error:
            raise self.close_error
        self.closed = True


class FakeConnection:
    def __init__(self, *, cursor=None, cursor_error=None, rollback_error=None):
        self.cursor_object = cursor or FakeCursor()
        self.cursor_error = cursor_error
        self.rollback_error = rollback_error
        self.rollback_calls = 0

    def cursor(self, **_kwargs):
        if self.cursor_error:
            raise self.cursor_error
        return self.cursor_object

    def rollback(self):
        self.rollback_calls += 1
        if self.rollback_error:
            raise self.rollback_error


class FakePool:
    def __init__(self, connection, *, put_error=None):
        self.connection = connection
        self.put_error = put_error
        self.getconn_calls = 0
        self.putconn_calls = []

    def getconn(self):
        self.getconn_calls += 1
        return self.connection

    def putconn(self, connection, close=False):
        self.putconn_calls.append((connection, close))
        if self.put_error and not close:
            raise self.put_error


class DatabaseConnectionTests(unittest.TestCase):
    def setUp(self):
        database.get_db_pool.cache_clear()

    def tearDown(self):
        database.get_db_pool.cache_clear()

    def test_normal_read_closes_cursor_rolls_back_and_returns_connection(self):
        cursor = FakeCursor()
        connection = FakeConnection(cursor=cursor)
        pool = FakePool(connection)

        with patch.object(database, "get_db_pool", return_value=pool):
            with database.get_db_connection() as active_cursor:
                self.assertIs(active_cursor, cursor)

        self.assertTrue(cursor.closed)
        self.assertEqual(connection.rollback_calls, 1)
        self.assertEqual(pool.putconn_calls, [(connection, False)])

    def test_route_exception_rolls_back_and_preserves_original_exception(self):
        connection = FakeConnection()
        pool = FakePool(connection)
        route_error = ValueError("route failed")

        with patch.object(database, "get_db_pool", return_value=pool):
            with self.assertRaises(ValueError) as raised:
                with database.get_db_connection():
                    raise route_error

        self.assertIs(raised.exception, route_error)
        self.assertEqual(connection.rollback_calls, 1)
        self.assertEqual(pool.putconn_calls, [(connection, False)])

    def test_rollback_failure_discards_connection(self):
        connection = FakeConnection(rollback_error=RuntimeError("rollback failed"))
        pool = FakePool(connection)

        with patch.object(database, "get_db_pool", return_value=pool):
            with self.assertRaisesRegex(RuntimeError, "rollback failed"):
                with database.get_db_connection():
                    pass

        self.assertEqual(connection.rollback_calls, 1)
        self.assertEqual(pool.putconn_calls, [(connection, True)])

    def test_cursor_construction_failure_is_handled_safely(self):
        connection = FakeConnection(cursor_error=RuntimeError("cursor failed"))
        pool = FakePool(connection)

        with patch.object(database, "get_db_pool", return_value=pool):
            with self.assertRaisesRegex(RuntimeError, "cursor failed"):
                with database.get_db_connection():
                    pass

        self.assertEqual(connection.rollback_calls, 1)
        self.assertEqual(pool.putconn_calls, [(connection, False)])

    def test_cursor_cleanup_failure_discards_connection(self):
        connection = FakeConnection(
            cursor=FakeCursor(close_error=RuntimeError("close failed"))
        )
        pool = FakePool(connection)

        with patch.object(database, "get_db_pool", return_value=pool):
            with self.assertRaisesRegex(RuntimeError, "close failed"):
                with database.get_db_connection():
                    pass

        self.assertEqual(connection.rollback_calls, 0)
        self.assertEqual(pool.putconn_calls, [(connection, True)])

    def test_pool_creation_is_cached_across_successful_calls(self):
        connection = FakeConnection()
        pool = FakePool(connection)

        with patch.object(
            database,
            "create_threaded_connection_pool",
            return_value=pool,
        ) as create_pool:
            with database.get_db_connection():
                pass
            with database.get_db_connection():
                pass

        create_pool.assert_called_once_with()
        self.assertEqual(pool.getconn_calls, 2)


if __name__ == "__main__":
    unittest.main()
