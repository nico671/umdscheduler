import os
import sqlite3
from pathlib import Path

from flask_restful import Resource, reqparse
from resources.courses.utils.all_courses_utils import (
    int_or_string,
    validate_geneds,
    validate_min_credits,
    validate_semester,
)


def get_all_courses(
    semester, min_credits, min_credits_comparator, dept_id=None, gen_eds=None
):
    project_root = Path(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
    db_path = project_root / "db" / "courses.sqlite"

    if not db_path.exists():
        raise ValueError(
            "Database not found. Please run the scraper first to populate the database."
        )

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    c = conn.cursor()

    try:
        # Build the base query
        query = """
        SELECT DISTINCT 
            c.course_id,
            c.course_name,
            c.course_credits,
            c.grading_method as course_grading_method,
            c.description as course_description,
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
        """

        params = []
        conditions = []

        # Add department filter
        if dept_id:
            conditions.append("d.dept_code = ?")
            params.append(dept_id)

        # Add credits filter
        if min_credits_comparator:
            if min_credits_comparator == "eq":
                conditions.append("c.course_credits = ?")
            elif min_credits_comparator == "lt":
                conditions.append("c.course_credits < ?")
            elif min_credits_comparator == "gt":
                conditions.append("c.course_credits > ?")
            elif min_credits_comparator == "geq":
                conditions.append("c.course_credits >= ?")
            elif min_credits_comparator == "leq":
                conditions.append("c.course_credits <= ?")
            params.append(min_credits)
        else:
            conditions.append("c.course_credits >= ?")
            params.append(min_credits)

        # Add gen_eds filter
        if gen_eds:
            placeholders = ",".join("?" * len(gen_eds))
            conditions.append(f"""
                c.id IN (
                    SELECT DISTINCT cg.course_id 
                    FROM course_geneds cg 
                    JOIN geneds g ON cg.gened_id = g.id 
                    WHERE g.name IN ({placeholders})
                )
            """)
            params.extend(gen_eds)

        # Combine conditions
        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY d.dept_code, c.course_id"

        c.execute(query, params)
        rows = c.fetchall()

        all_courses = []
        for row in rows:
            # Get geneds for this course
            c.execute(
                """
                SELECT g.name 
                FROM geneds g 
                JOIN course_geneds cg ON g.id = cg.gened_id 
                WHERE cg.course_id = ?
            """,
                (row["course_id"],),
            )

            gened_rows = c.fetchall()
            gened_list = [gened["name"] for gened in gened_rows]

            # Build the course object
            curr_course = {
                "course_id": row["course_id"],
                "course_name": row["course_name"],
                "course_credits": str(
                    row["course_credits"]
                ),  # Keep as string for consistency
                "course_grading_method": row["course_grading_method"],
                "dept_code": row["dept_code"],
                "dept_name": row["dept_name"],
                "geneds": gened_list,
                "course_description": row["course_description"] or "",
                "additional_info": {
                    "prerequisites": row["prerequisites"] or "",
                    "corequisites": row["corequisites"] or "",
                    "restrictions": row["restrictions"] or "",
                    "formerly": row["formerly"] or "",
                    "crosslisted_as": row["crosslisted_as"] or "",
                    "credit_granted_for": row["credit_granted_for"] or "",
                    "additional_info": [],  # This was for extra unstructured info
                },
            }
            all_courses.append(curr_course)

        return all_courses

    except sqlite3.Error as e:
        raise ValueError(f"Database error: {e}")
    finally:
        conn.close()


class AllCoursesList(Resource):
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
            "min_credits",
            type=str,
            required=True,
            help='min_credits parameter can be a number (default: <=) or in format "<number>|<comparator>" (eq, lt, gt, geq, leq)',
            location="args",
        )
        parser.add_argument(
            "dept_id",
            type=str,
            required=False,
            help='4-letter department code (e.g., "CMSC")',
            location="args",
        )
        parser.add_argument(
            "gen_ed",
            type=str,
            required=False,
            help='GenEd requirement code (e.g., "DSNS"). To provide multiple codes, use a comma-separated list (e.g., "DSNS,DSNL")',
            location="args",
        )
        args = parser.parse_args()

        try:
            semester = validate_semester(args["semester"])
            min_credits, min_credits_comparator = validate_min_credits(
                args["min_credits"]
            )
            dept_id = args.get("dept_id")
            gened_list = validate_geneds(args.get("gen_ed"))

            all_courses = get_all_courses(
                semester,
                min_credits,
                min_credits_comparator,
                dept_id=dept_id,
                gen_eds=gened_list,
            )

            if not all_courses:
                return {"message": "No courses found for the given parameters."}, 404
            return {"courses": all_courses}, 200

        except ValueError as e:
            return {"error": str(e)}, 400
        except Exception:
            return {
                "error": "An unexpected error occurred while fetching courses."
            }, 500
        args = parser.parse_args()
        semester = validate_semester(args["semester"])
        min_credits, min_credits_comparator = validate_min_credits(args["min_credits"])
        dept_id = args.get("dept_id")
        gened_list = validate_geneds(args.get("gen_ed"))
        all_courses = get_all_courses(
            semester,
            min_credits,
            min_credits_comparator,
            dept_id=dept_id,
            gen_eds=gened_list,
        )
        # print(all_courses)
        if not all_courses:
            return {"message": "No courses found for the given parameters."}, 404
        return {"courses": all_courses}, 200
