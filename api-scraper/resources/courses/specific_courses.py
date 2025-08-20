import os
import sqlite3
from pathlib import Path

from flask_restful import Resource, reqparse
from resources.courses.utils.all_courses_utils import (
    int_or_string,
    validate_semester,
    validate_course_ids,
)


def get_specific_courses(semester, course_ids):
    """
    Get specific courses by their course IDs.
    
    Args:
        semester: Semester code (optional for validation)
        course_ids: List of course IDs to retrieve
    
    Returns:
        Dict containing found courses, missing courses, and counts
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
        # Build query with placeholders for each course ID
        placeholders = ",".join("?" for _ in course_ids)
        query = f"""
        SELECT DISTINCT 
            c.id as course_db_id,
            c.course_id,
            c.course_name,
            c.course_credits,
            c.grading_method,
            c.description,
            c.prerequisites,
            c.corequisites,
            c.restrictions,
            c.formerly,
            c.crosslisted_as,
            c.credit_granted_for,
            d.dept_code,
            d.dept_name
        FROM courses c
        JOIN departments d ON c.dept_id = d.id
        WHERE c.course_id IN ({placeholders})
        ORDER BY d.dept_code, c.course_id
        """

        c.execute(query, course_ids)
        rows = c.fetchall()

        courses = []
        found_course_ids = set()
        
        for row in rows:
            found_course_ids.add(row["course_id"])
            
            # Get general education requirements for this course
            c.execute(
                """
                SELECT g.name 
                FROM geneds g
                JOIN course_geneds cg ON g.id = cg.gened_id
                WHERE cg.course_id = ?
                """,
                (row["course_db_id"],)
            )
            geneds = [gened[0] for gened in c.fetchall()]

            # Get sections for this course (basic info only)
            c.execute(
                """
                SELECT s.section_id, s.total_seats, s.open_seats, s.waitlist_count
                FROM sections s
                WHERE s.course_id = ?
                ORDER BY s.section_id
                """,
                (row["course_db_id"],)
            )
            sections = []
            for section_row in c.fetchall():
                sections.append({
                    "section_id": section_row["section_id"],
                    "total_seats": section_row["total_seats"],
                    "open_seats": section_row["open_seats"],
                    "waitlist_count": section_row["waitlist_count"]
                })

            course_data = {
                "course_id": row["course_id"],
                "course_name": row["course_name"],
                "course_credits": row["course_credits"],
                "grading_method": row["grading_method"],
                "description": row["description"],
                "prerequisites": row["prerequisites"],
                "corequisites": row["corequisites"],
                "restrictions": row["restrictions"],
                "formerly": row["formerly"],
                "crosslisted_as": row["crosslisted_as"],
                "credit_granted_for": row["credit_granted_for"],
                "department": {
                    "dept_code": row["dept_code"],
                    "dept_name": row["dept_name"]
                },
                "geneds": geneds,
                "sections": sections,
                "section_count": len(sections)
            }
            courses.append(course_data)

        # Check for missing course IDs
        missing_course_ids = set(course_ids) - found_course_ids
        
        result = {
            "found_courses": courses,
            "found_count": len(courses),
            "requested_count": len(course_ids)
        }
        
        if missing_course_ids:
            result["missing_course_ids"] = list(missing_course_ids)
            result["missing_count"] = len(missing_course_ids)

        return result

    except sqlite3.Error as e:
        raise ValueError(f"Database error: {e}")
    finally:
        conn.close()


class SpecificCourses(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "course_ids",
            type=str,
            required=True,
            location="args",
            help="Comma-separated list of course IDs in format DEPTNNN with optional trailing characters (e.g., 'ENGL101,MATH140,CMSC388F')",
        )
        parser.add_argument(
            "semester",
            type=int_or_string,
            required=False,
            location="args",
            help="6-digit semester ID (optional, used for validation if provided)",
        )

        try:
            args = parser.parse_args()
            
            # Validate and parse course IDs
            course_ids = validate_course_ids(args["course_ids"])
            
            # Validate semester if provided
            semester = None
            if args.get("semester"):
                semester = validate_semester(args["semester"])

            # Get courses
            result = get_specific_courses(semester, course_ids)

            if result["found_count"] == 0:
                return {
                    "message": "No courses found with the provided course IDs",
                    "data": result
                }, 404

            response_message = f"Found {result['found_count']} out of {result['requested_count']} requested courses"
            if result.get("missing_count", 0) > 0:
                response_message += f". {result['missing_count']} course(s) not found."

            return {
                "message": response_message,
                "data": result
            }, 200

        except ValueError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            return {"error": "An internal server error occurred"}, 500
