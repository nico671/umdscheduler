from typing import List, Optional

from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware

from api.database import get_db_connection
from api.scheduler import build_schedules
from api.schemas import (
    CourseDetail,
    CourseSummary,
    Department,
    ScheduleRequest,
    ScheduleResult,
    SectionSearchResult,
    Semester,
    StatusResponse,
)

app = FastAPI(title="UMD API", version="0.0.1")

# Add this block:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace "*" with your frontend's actual URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _get_active_or_latest_semester_code(cursor) -> Optional[str]:
    cursor.execute(
        """
        SELECT semester_code
        FROM semesters
        WHERE is_active = TRUE
        ORDER BY semester_code DESC
        LIMIT 1
    """
    )
    row = cursor.fetchone()
    if row:
        return row["semester_code"]

    cursor.execute(
        """
        SELECT semester_code
        FROM semesters
        ORDER BY semester_code DESC
        LIMIT 1
    """
    )
    row = cursor.fetchone()
    return row["semester_code"] if row else None


def _resolve_semester(cursor, semester: Optional[str]) -> str:
    if semester:
        return semester.strip()

    resolved = _get_active_or_latest_semester_code(cursor)
    if not resolved:
        raise HTTPException(status_code=404, detail="No semester data available")
    return resolved


@app.get("/api/v1/status", response_model=StatusResponse)
def get_status():
    """
    Returns freshness status based on the most recent section update timestamp.
    """
    with get_db_connection() as cursor:
        cursor.execute("SELECT MAX(last_updated) AS last_updated FROM sections")
        row = cursor.fetchone()
        return {"last_updated": row["last_updated"] if row else None}


@app.get("/api/v1/semesters", response_model=List[Semester])
def get_semesters(active_only: bool = Query(default=False)):
    """
    Returns available semesters, newest first.
    """
    with get_db_connection() as cursor:
        query = """
            SELECT semester_code, name, is_active
            FROM semesters
        """
        params = []

        if active_only:
            query += " WHERE is_active = TRUE"

        query += " ORDER BY semester_code DESC"

        cursor.execute(query, params)
        return cursor.fetchall()


@app.get("/api/v1/departments", response_model=List[Department])
def get_departments(response: Response):
    """
    Returns all department codes and names.
    """
    # Aggressive caching: departments rarely change.
    response.headers["Cache-Control"] = "public, max-age=86400"

    with get_db_connection() as cursor:
        cursor.execute(
            """
            SELECT department_code, name
            FROM departments
            ORDER BY department_code ASC
        """
        )
        return cursor.fetchall()


@app.get("/api/v1/courses", response_model=List[CourseSummary])
def search_courses(
    semester: Optional[str] = None,
    department: Optional[str] = None,
    credits: Optional[str] = None,
    gened: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """
    Course discovery endpoint (top-level course data only, no nested sections).
    """
    with get_db_connection() as cursor:
        resolved_semester = _resolve_semester(cursor, semester)
        where_clauses = [
            """
            EXISTS (
                SELECT 1
                FROM sections s
                WHERE s.course_code = c.course_code
                  AND s.semester_code = %s
            )
            """
        ]
        params = [resolved_semester]

        if department:
            where_clauses.append("c.department_code = %s")
            params.append(department.upper().strip())

        if credits is not None:
            where_clauses.append("c.credits = %s")
            params.append(str(credits))

        if gened:
            where_clauses.append("%s = ANY(c.gened_codes)")
            params.append(gened.upper().strip())

        if search:
            where_clauses.append("(c.title ILIKE %s OR c.description ILIKE %s)")
            search_term = f"%{search.strip()}%"
            params.extend([search_term, search_term])

        query = f"""
            SELECT
                c.course_code,
                c.department_code,
                c.title,
                c.credits,
                c.description,
                c.grading_options,
                c.gened_codes,
                c.attributes
            FROM courses c
            WHERE {" AND ".join(where_clauses)}
            ORDER BY c.course_code ASC
            LIMIT %s OFFSET %s
        """

        params.extend([limit, offset])
        cursor.execute(query, params)
        return cursor.fetchall()


@app.get("/api/v1/courses/{course_code}", response_model=CourseDetail)
def get_course(course_code: str, semester: Optional[str] = None):
    """
    Fetches a specific course, its sections for a semester, and meeting times.
    """
    # Force uppercase for consistency (e.g., 'aaas100' -> 'AAAS100')
    course_code = course_code.upper()

    with get_db_connection() as cursor:
        resolved_semester = _resolve_semester(cursor, semester)

        # 1. Fetch the catalog data
        cursor.execute("SELECT * FROM courses WHERE course_code = %s", (course_code,))
        course_row = cursor.fetchone()

        if not course_row:
            # Best Practice: Return a proper 404 if it doesn't exist
            raise HTTPException(status_code=404, detail="Course not found")

        # 2. Fetch the sections
        cursor.execute(
            """
            SELECT id, section_code, instructors, total_seats, open_seats, waitlist 
            FROM sections 
            WHERE course_code = %s AND semester_code = %s
        """,
            (course_code, resolved_semester),
        )
        sections = cursor.fetchall()

        # 3. Fetch the meetings for those sections
        for section in sections:
            cursor.execute(
                """
                SELECT days, start_time, end_time, building_code, room, class_type 
                FROM section_meetings 
                WHERE section_id = %s
            """,
                (section["id"],),
            )
            section["meetings"] = cursor.fetchall()

        # Attach sections to the main course object
        course_row["sections"] = sections

        # FastAPI and Pydantic will automatically validate this dictionary
        # and convert it to perfect JSON
        return course_row


@app.get("/api/v1/sections", response_model=List[SectionSearchResult])
def search_sections(
    semester: Optional[str] = None,
    status: Optional[str] = None,
    instructor: Optional[str] = None,
    days: Optional[str] = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """
    Searches specific sections by availability/instructor/meeting-day constraints.
    """
    with get_db_connection() as cursor:
        resolved_semester = _resolve_semester(cursor, semester)

        where_clauses = ["s.semester_code = %s"]
        params = [resolved_semester]

        if status:
            normalized_status = status.strip().lower()
            if normalized_status == "open":
                where_clauses.append("s.open_seats > 0")
            elif normalized_status == "closed":
                where_clauses.append("s.open_seats <= 0")
            else:
                raise HTTPException(
                    status_code=422,
                    detail="Invalid status. Use 'open' or 'closed'.",
                )

        if instructor:
            where_clauses.append(
                """
                EXISTS (
                    SELECT 1
                    FROM unnest(s.instructors) AS i
                    WHERE i ILIKE %s
                )
                """
            )
            params.append(f"%{instructor.strip()}%")

        if days:
            where_clauses.append(
                """
                EXISTS (
                    SELECT 1
                    FROM section_meetings sm2
                    WHERE sm2.section_id = s.id
                      AND sm2.days ILIKE %s
                )
                """
            )
            params.append(f"%{days.strip()}%")

        query = f"""
            SELECT
                c.course_code,
                c.title AS course_title,
                s.semester_code,
                s.section_code,
                s.instructors,
                s.total_seats,
                s.open_seats,
                s.waitlist,
                COALESCE(
                    json_agg(
                        json_build_object(
                            'days', sm.days,
                            'start_time', sm.start_time,
                            'end_time', sm.end_time,
                            'building_code', sm.building_code,
                            'room', sm.room,
                            'class_type', sm.class_type
                        )
                    ) FILTER (WHERE sm.id IS NOT NULL),
                    '[]'::json
                ) AS meetings
            FROM sections s
            JOIN courses c ON c.course_code = s.course_code
            LEFT JOIN section_meetings sm ON sm.section_id = s.id
            WHERE {" AND ".join(where_clauses)}
            GROUP BY
                c.course_code,
                c.title,
                s.semester_code,
                s.section_code,
                s.instructors,
                s.total_seats,
                s.open_seats,
                s.waitlist
            ORDER BY c.course_code ASC, s.section_code ASC
            LIMIT %s OFFSET %s
        """

        params.extend([limit, offset])
        cursor.execute(query, params)
        return cursor.fetchall()


@app.post("/api/v1/schedules", response_model=List[ScheduleResult])
def generate_schedules(payload: ScheduleRequest):
    """
    Builds conflict-free schedules for required courses in a semester,
    optionally filtering by excluded professors and blocked time windows.
    """
    if not payload.required_courses:
        raise HTTPException(
            status_code=422,
            detail="required_courses must include at least one course code.",
        )

    normalized_courses = [
        c.strip().upper() for c in payload.required_courses if c.strip()
    ]
    if not normalized_courses:
        raise HTTPException(
            status_code=422,
            detail="required_courses must include at least one non-empty course code.",
        )

    with get_db_connection() as cursor:
        resolved_semester = _resolve_semester(cursor, payload.semester)

    parsed_time_constraints = [
        (tc.day, tc.start_time, tc.end_time) for tc in payload.time_constraints
    ]

    return build_schedules(
        required_courses=normalized_courses,
        semester=resolved_semester,
        excluded_profs=payload.excluded_profs,
        time_constraints=parsed_time_constraints,
        max_schedules=payload.max_schedules,
    )
