import os
import sqlite3
from pathlib import Path

from flask_restful import Resource, reqparse
from resources.courses.utils.all_courses_utils import (
    int_or_string,
    validate_semester,
    validate_seats,
)


def validate_course_id(course_id, semester):
    """
    Validate that the course_id exists in the database.
    Returns the course database ID if valid, raises ValueError if not.
    """
    project_root = Path(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    db_path = project_root / "db" / "courses.sqlite"

    if not db_path.exists():
        raise ValueError(
            "Database not found. Please run the scraper first to populate the database."
        )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        # Check if course exists
        c.execute(
            """
            SELECT c.id, c.course_id, c.course_name, d.dept_code 
            FROM courses c
            JOIN departments d ON c.dept_id = d.id
            WHERE c.course_id = ?
            """,
            (course_id,)
        )
        result = c.fetchone()
        
        if not result:
            raise ValueError(f"Course ID '{course_id}' not found in database.")
        
        return result["id"]
    
    except sqlite3.Error as e:
        raise ValueError(f"Database error: {e}")
    finally:
        conn.close()


def get_course_sections(
    semester, course_id, total_seats=None, total_seats_comparator=None,
    open_seats=None, open_seats_comparator=None, 
    waitlist_count=None, waitlist_count_comparator=None
):
    """
    Get sections for a specific course with optional seat filtering.
    """
    project_root = Path(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    db_path = project_root / "db" / "courses.sqlite"

    if not db_path.exists():
        raise ValueError(
            "Database not found. Please run the scraper first to populate the database."
        )

    # Validate course exists
    course_db_id = validate_course_id(course_id, semester)

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    try:
        # Build the base query
        query = """
        SELECT DISTINCT 
            s.id as section_db_id,
            s.section_id,
            s.total_seats,
            s.open_seats,
            s.waitlist_count,
            c.course_id,
            c.course_name,
            c.course_credits,
            c.grading_method,
            d.dept_code,
            d.dept_name
        FROM sections s
        JOIN courses c ON s.course_id = c.id
        JOIN departments d ON c.dept_id = d.id
        WHERE c.course_id = ?
        """

        params = [course_id]
        conditions = []

        # Add seat filters
        if total_seats is not None:
            if total_seats_comparator == "eq":
                conditions.append("s.total_seats = ?")
            elif total_seats_comparator == "lt":
                conditions.append("s.total_seats < ?")
            elif total_seats_comparator == "gt":
                conditions.append("s.total_seats > ?")
            elif total_seats_comparator == "geq":
                conditions.append("s.total_seats >= ?")
            elif total_seats_comparator == "leq":
                conditions.append("s.total_seats <= ?")
            params.append(total_seats)

        if open_seats is not None:
            if open_seats_comparator == "eq":
                conditions.append("s.open_seats = ?")
            elif open_seats_comparator == "lt":
                conditions.append("s.open_seats < ?")
            elif open_seats_comparator == "gt":
                conditions.append("s.open_seats > ?")
            elif open_seats_comparator == "geq":
                conditions.append("s.open_seats >= ?")
            elif open_seats_comparator == "leq":
                conditions.append("s.open_seats <= ?")
            params.append(open_seats)

        if waitlist_count is not None:
            if waitlist_count_comparator == "eq":
                conditions.append("s.waitlist_count = ?")
            elif waitlist_count_comparator == "lt":
                conditions.append("s.waitlist_count < ?")
            elif waitlist_count_comparator == "gt":
                conditions.append("s.waitlist_count > ?")
            elif waitlist_count_comparator == "geq":
                conditions.append("s.waitlist_count >= ?")
            elif waitlist_count_comparator == "leq":
                conditions.append("s.waitlist_count <= ?")
            params.append(waitlist_count)

        # Combine conditions
        if conditions:
            query += " AND " + " AND ".join(conditions)

        query += " ORDER BY s.section_id"

        c.execute(query, params)
        rows = c.fetchall()

        sections = []
        for row in rows:
            # Get instructors for this section
            c.execute(
                "SELECT instructor_name FROM section_instructors WHERE section_id = ?",
                (row["section_db_id"],)
            )
            instructors = [inst[0] for inst in c.fetchall()]

            # Get meeting times for this section
            c.execute(
                """
                SELECT meeting_days, start_time, end_time, building, class_type 
                FROM meeting_times WHERE section_id = ?
                """,
                (row["section_db_id"],)
            )
            meeting_times = []
            for mt in c.fetchall():
                meeting_times.append({
                    "meeting_days": mt["meeting_days"],
                    "start_time": mt["start_time"],
                    "end_time": mt["end_time"],
                    "building": mt["building"],
                    "class_type": mt["class_type"]
                })

            section_data = {
                "section_id": row["section_id"],
                "total_seats": row["total_seats"],
                "open_seats": row["open_seats"],
                "waitlist_count": row["waitlist_count"],
                "instructors": instructors,
                "meeting_times": meeting_times,
                "course_info": {
                    "course_id": row["course_id"],
                    "course_name": row["course_name"],
                    "course_credits": row["course_credits"],
                    "grading_method": row["grading_method"],
                    "dept_code": row["dept_code"],
                    "dept_name": row["dept_name"]
                }
            }
            sections.append(section_data)

        return sections

    except sqlite3.Error as e:
        raise ValueError(f"Database error: {e}")
    finally:
        conn.close()


class CourseSections(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "semester",
            type=int_or_string,
            required=True,
            location="args",
            help="Semester code is required, use the courses/semesters endpoint to get available semesters",
        )
        parser.add_argument(
            "course_id",
            type=str,
            required=True,
            location="args",
            help="Course ID is required (e.g., 'CMSC131')",
        )
        parser.add_argument(
            "total_seats",
            type=str,
            required=False,
            help='total_seats parameter can be a number (default: >=) or in format "<number>|<comparator>" (eq, lt, gt, geq, leq)',
            location="args",
        )
        parser.add_argument(
            "open_seats",
            type=str,
            required=False,
            help='open_seats parameter can be a number (default: >=) or in format "<number>|<comparator>" (eq, lt, gt, geq, leq)',
            location="args",
        )
        parser.add_argument(
            "waitlist_count",
            type=str,
            required=False,
            help='waitlist_count parameter can be a number (default: >=) or in format "<number>|<comparator>" (eq, lt, gt, geq, leq)',
            location="args",
        )

        try:
            args = parser.parse_args()
            
            # Validate required parameters
            semester = validate_semester(args["semester"])
            course_id = args["course_id"].upper()  # Normalize to uppercase

            # Validate optional seat parameters
            total_seats = None
            total_seats_comparator = None
            if args.get("total_seats"):
                total_seats, total_seats_comparator = validate_seats(args["total_seats"], "total_seats")

            open_seats = None
            open_seats_comparator = None
            if args.get("open_seats"):
                open_seats, open_seats_comparator = validate_seats(args["open_seats"], "open_seats")

            waitlist_count = None
            waitlist_count_comparator = None
            if args.get("waitlist_count"):
                waitlist_count, waitlist_count_comparator = validate_seats(args["waitlist_count"], "waitlist_count")

            # Get sections
            sections = get_course_sections(
                semester,
                course_id,
                total_seats=total_seats,
                total_seats_comparator=total_seats_comparator,
                open_seats=open_seats,
                open_seats_comparator=open_seats_comparator,
                waitlist_count=waitlist_count,
                waitlist_count_comparator=waitlist_count_comparator,
            )

            if not sections:
                return {
                    "message": f"No sections found for course {course_id} with the specified criteria",
                    "data": []
                }, 404

            return {
                "message": f"Found {len(sections)} sections for course {course_id}",
                "data": sections
            }, 200

        except ValueError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            return {"error": "An internal server error occurred"}, 500
