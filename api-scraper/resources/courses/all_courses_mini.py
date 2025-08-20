import os
import sqlite3
from pathlib import Path

from flask_restful import Resource, reqparse
from resources.courses.utils.all_courses_utils import (
    int_or_string,
    validate_semester,
)


def get_all_courses_mini(semester):
    """
    Fetch all courses from the SQLite database.
    Note: semester parameter is kept for API compatibility but not used
    since the database contains current semester data.
    """
    project_root = Path(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    db_path = project_root / "db" / "courses.sqlite"

    if not db_path.exists():
        raise ValueError(f"Database not found at {db_path}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This allows dict-like access to rows
    c = conn.cursor()

    try:
        # Query to get all courses with their department information
        c.execute("""
            SELECT c.course_id, c.course_name, d.dept_code
            FROM courses c
            JOIN departments d ON c.dept_id = d.id
            ORDER BY d.dept_code, c.course_id
        """)

        rows = c.fetchall()
        all_courses = []

        for row in rows:
            all_courses.append(
                {
                    "course_code": row["course_id"],
                    "course_name": row["course_name"],
                }
            )

        return all_courses

    finally:
        conn.close()


class AllCoursesListMini(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "semester",
            type=int_or_string,
            required=True,
            location="args",
            help="Semester code is required, use the courses/semesters endpoint to get available semesters",
        )

        args = parser.parse_args()
        semester = validate_semester(args["semester"])

        all_courses = get_all_courses_mini(semester)
        if not all_courses:
            return {"message": "No courses found for the given parameters."}, 404
        return {"courses": all_courses}, 200
