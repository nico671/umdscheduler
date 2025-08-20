import os
import sqlite3
from pathlib import Path

from flask_restful import Resource, reqparse
from resources.courses.utils.all_courses_utils import (
    int_or_string,
    validate_semester,
    validate_section_ids,
)


def get_specific_sections(semester, section_ids):
    """
    Get specific sections by their section IDs.
    
    Args:
        semester: Semester code (optional for validation)
        section_ids: List of section IDs to retrieve
    
    Returns:
        List of section data with course info, instructors, and meeting times
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
        # Build query with placeholders for each section ID
        placeholders = ",".join("?" for _ in section_ids)
        query = f"""
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
            c.description,
            c.prerequisites,
            c.corequisites,
            c.restrictions,
            c.formerly,
            c.crosslisted_as,
            c.credit_granted_for,
            d.dept_code,
            d.dept_name
        FROM sections s
        JOIN courses c ON s.course_id = c.id
        JOIN departments d ON c.dept_id = d.id
        WHERE s.section_id IN ({placeholders})
        ORDER BY s.section_id
        """

        c.execute(query, section_ids)
        rows = c.fetchall()

        sections = []
        found_section_ids = set()
        
        for row in rows:
            found_section_ids.add(row["section_id"])
            
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

            # Get general education requirements for this course
            c.execute(
                """
                SELECT g.name 
                FROM geneds g
                JOIN course_geneds cg ON g.id = cg.gened_id
                WHERE cg.course_id = ?
                """,
                (row["section_db_id"],)
            )
            geneds = [gened[0] for gened in c.fetchall()]

            section_data = {
                "section_id": row["section_id"],
                "total_seats": row["total_seats"],
                "open_seats": row["open_seats"],
                "waitlist_count": row["waitlist_count"],
                "instructors": instructors,
                "meeting_times": meeting_times,
                "course": {
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
                    "dept_code": row["dept_code"],
                    "dept_name": row["dept_name"],
                    "geneds": geneds
                }
            }
            sections.append(section_data)

        # Check for missing section IDs
        missing_section_ids = set(section_ids) - found_section_ids
        
        result = {
            "found_sections": sections,
            "found_count": len(sections),
            "requested_count": len(section_ids)
        }
        
        if missing_section_ids:
            result["missing_section_ids"] = list(missing_section_ids)
            result["missing_count"] = len(missing_section_ids)

        return result

    except sqlite3.Error as e:
        raise ValueError(f"Database error: {e}")
    finally:
        conn.close()


class SpecificSections(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "section_ids",
            type=str,
            required=True,
            location="args",
            help="Comma-separated list of section IDs in format DEPTNNN-XXXX (e.g., 'CMSC131-0101,ENGL101-0201')",
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
            
            # Validate and parse section IDs
            section_ids = validate_section_ids(args["section_ids"])
            
            # Validate semester if provided
            semester = None
            if args.get("semester"):
                semester = validate_semester(args["semester"])

            # Get sections
            result = get_specific_sections(semester, section_ids)

            if result["found_count"] == 0:
                return {
                    "message": "No sections found with the provided section IDs",
                    "data": result
                }, 404

            response_message = f"Found {result['found_count']} out of {result['requested_count']} requested sections"
            if result.get("missing_count", 0) > 0:
                response_message += f". {result['missing_count']} section(s) not found."

            return {
                "message": response_message,
                "data": result
            }, 200

        except ValueError as e:
            return {"error": str(e)}, 400
        except Exception as e:
            return {"error": "An internal server error occurred"}, 500
