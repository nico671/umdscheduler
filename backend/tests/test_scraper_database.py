import inspect
import os
import unittest
from unittest.mock import patch

from scraper import dbmanager


class FakeCursor:
    def __init__(self, *, lock_result=True, fail_on=None):
        self.lock_result = lock_result
        self.fail_on = fail_on
        self.executed = []

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        return False

    def execute(self, sql, params=None):
        self.executed.append((sql, params))
        if self.fail_on and self.fail_on in sql:
            raise RuntimeError("database write failed")

    def fetchone(self):
        return (self.lock_result,)


class FakeConnection:
    def __init__(self, *, lock_result=True, fail_on=None):
        self.autocommit = True
        self.cursor_object = FakeCursor(lock_result=lock_result, fail_on=fail_on)
        self.commit_count = 0
        self.rollback_count = 0
        self.close_count = 0

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        return False

    def cursor(self):
        return self.cursor_object

    def commit(self):
        self.commit_count += 1

    def rollback(self):
        self.rollback_count += 1

    def close(self):
        self.close_count += 1


def sample_courses(section_codes=("001",)):
    return [
        {
            "course_code": "CMSC131",
            "course_name": "Intro",
            "course_credits": "3",
            "description": "Course",
            "grading_options": [],
            "gened_codes": [],
            "attributes": {},
            "sections": [
                {
                    "section_code": code,
                    "instructors": [],
                    "total_seats": "30",
                    "open_seats": "30",
                    "waitlist_count": "0",
                    "time_info": [],
                }
                for code in section_codes
            ],
        }
    ]


class ScraperDatabaseUnitTests(unittest.TestCase):
    def setUp(self):
        self.execute_values_rows = [
            (1, "CMSC131", "001"),
        ]

    def _patch_database_helpers(self, connection):
        return (
            patch.object(dbmanager, "get_connection", return_value=connection),
            patch.object(dbmanager, "execute_batch"),
            patch.object(
                dbmanager,
                "execute_values",
                return_value=self.execute_values_rows,
            ),
        )

    def test_database_exception_rolls_back_transaction(self):
        connection = FakeConnection(fail_on="CREATE TABLE")
        patches = self._patch_database_helpers(connection)
        with patches[0], patches[1], patches[2]:
            with self.assertRaisesRegex(RuntimeError, "database write failed"):
                dbmanager.sync_scraped_data(
                    [("CMSC", "Computer")], "202601", sample_courses()
                )

        self.assertEqual(connection.commit_count, 0)
        self.assertEqual(connection.rollback_count, 1)
        self.assertEqual(connection.close_count, 1)

    def test_lock_conflict_rolls_back_without_data_operations(self):
        connection = FakeConnection(lock_result=False)
        patches = self._patch_database_helpers(connection)
        with patches[0], patches[1], patches[2]:
            with self.assertRaisesRegex(RuntimeError, "already publishing"):
                dbmanager.sync_scraped_data(
                    [("CMSC", "Computer")], "202601", sample_courses()
                )

        self.assertEqual(len(connection.cursor_object.executed), 1)
        self.assertEqual(connection.commit_count, 0)
        self.assertEqual(connection.rollback_count, 1)

    def test_sync_has_one_commit_after_processing(self):
        source = inspect.getsource(dbmanager.sync_scraped_data)
        self.assertEqual(source.count("conn.commit()"), 1)

    def test_duplicate_meetings_are_deduplicated_before_insert(self):
        courses = sample_courses()
        courses[0]["sections"][0]["time_info"] = [
            {
                "days": "MWF",
                "start_time": "9:00am",
                "end_time": "9:50am",
                "building_code": "IRB",
                "room": "0324",
                "class_type": "Lecture",
            },
            {
                "days": "MWF",
                "start_time": "9:00am",
                "end_time": "9:50am",
                "building_code": "IRB",
                "room": "0324",
                "class_type": "Lecture",
            },
        ]
        cursor = FakeCursor()
        with patch.object(
            dbmanager,
            "execute_values",
            return_value=self.execute_values_rows,
        ), patch.object(dbmanager, "execute_batch") as execute_batch:
            section_count, meeting_count = dbmanager._replace_sections(
                cursor, courses, "202601"
            )

        self.assertEqual((section_count, meeting_count), (1, 1))
        self.assertEqual(
            execute_batch.call_args.args[2],
            [(1, "MWF", "9:00am", "9:50am", "IRB", "0324", "Lecture")],
        )


@unittest.skipUnless(
    os.environ.get("TEST_DATABASE_URL"),
    "set TEST_DATABASE_URL to run PostgreSQL integration tests",
)
class ScraperDatabaseIntegrationTests(unittest.TestCase):
    semester_a = "999901"
    semester_b = "999902"

    @classmethod
    def setUpClass(cls):
        os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
        from common.settings import get_settings

        get_settings.cache_clear()

    @classmethod
    def tearDownClass(cls):
        connection = dbmanager.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM sections WHERE semester_code IN (%s, %s)",
                    (cls.semester_a, cls.semester_b),
                )
                cursor.execute(
                    "DELETE FROM semesters WHERE semester_code IN (%s, %s)",
                    (cls.semester_a, cls.semester_b),
                )
            connection.commit()
        finally:
            connection.close()

    def test_successful_sync_marks_only_new_semester_active(self):
        dbmanager.sync_scraped_data(
            [("CMSC", "Computer")], self.semester_a, sample_courses()
        )
        dbmanager.sync_scraped_data(
            [("CMSC", "Computer")], self.semester_b, sample_courses()
        )

        connection = dbmanager.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT semester_code, is_active
                    FROM semesters
                    WHERE semester_code IN (%s, %s)
                    ORDER BY semester_code
                    """,
                    (self.semester_a, self.semester_b),
                )
                rows = cursor.fetchall()
        finally:
            connection.close()

        self.assertEqual(rows, [(self.semester_a, False), (self.semester_b, True)])

    def test_replacing_semester_removes_stale_sections(self):
        dbmanager.sync_scraped_data(
            [("CMSC", "Computer")], self.semester_a, sample_courses(("001", "002"))
        )
        dbmanager.sync_scraped_data(
            [("CMSC", "Computer")], self.semester_a, sample_courses(("001",))
        )

        connection = dbmanager.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT section_code
                    FROM sections
                    WHERE semester_code = %s
                    ORDER BY section_code
                    """,
                    (self.semester_a,),
                )
                rows = cursor.fetchall()
        finally:
            connection.close()

        self.assertEqual(rows, [("001",)])

    def test_lock_conflict_does_not_change_data(self):
        dbmanager.sync_scraped_data(
            [("CMSC", "Computer")], self.semester_b, sample_courses()
        )
        before = dbmanager.get_connection()
        try:
            with before.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM sections WHERE semester_code = %s",
                    (self.semester_b,),
                )
                before_count = cursor.fetchone()[0]
        finally:
            before.close()

        holder = dbmanager.get_connection()
        holder.autocommit = False
        try:
            with holder.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_xact_lock(%s)",
                    (dbmanager.SCRAPER_ADVISORY_LOCK_KEY,),
                )
            with self.assertRaisesRegex(RuntimeError, "already publishing"):
                dbmanager.sync_scraped_data(
                    [("CMSC", "Computer")], self.semester_b, sample_courses()
                )
        finally:
            holder.rollback()
            holder.close()

        after = dbmanager.get_connection()
        try:
            with after.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM sections WHERE semester_code = %s",
                    (self.semester_b,),
                )
                after_count = cursor.fetchone()[0]
        finally:
            after.close()

        self.assertEqual(after_count, before_count)


if __name__ == "__main__":
    unittest.main()
