import json
import re
import sys
import time
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_batch, execute_values

try:
    from common.db_config import get_db_connect_params
except ModuleNotFoundError:
    backend_root = Path(__file__).resolve().parents[1]
    if str(backend_root) not in sys.path:
        sys.path.append(str(backend_root))
    from common.db_config import get_db_connect_params

PROGRESS_EVERY = 100
DEPT_CODE_RE = re.compile(r"^(?P<department>[A-Z]{4})")
SCRAPER_ADVISORY_LOCK_KEY = 7_613_042

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS semesters (
    semester_code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(50) NOT NULL,
    is_active BOOLEAN DEFAULT false
);

CREATE TABLE IF NOT EXISTS departments (
    department_code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE IF NOT EXISTS courses (
    course_code VARCHAR(20) PRIMARY KEY,
    department_code VARCHAR(10) REFERENCES departments(department_code),
    title VARCHAR(255),
    credits VARCHAR(20),
    description TEXT,
    grading_options TEXT[],
    gened_codes TEXT[],
    attributes JSONB,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sections (
    id SERIAL PRIMARY KEY,
    course_code VARCHAR(20) REFERENCES courses(course_code),
    semester_code VARCHAR(10) REFERENCES semesters(semester_code),
    section_code VARCHAR(10) NOT NULL,
    instructors TEXT[],
    total_seats INTEGER,
    open_seats INTEGER,
    waitlist INTEGER,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(course_code, semester_code, section_code)
);

CREATE TABLE IF NOT EXISTS section_meetings (
    id SERIAL PRIMARY KEY,
    section_id INTEGER REFERENCES sections(id) ON DELETE CASCADE,
    days VARCHAR(20),
    start_time VARCHAR(20),
    end_time VARCHAR(20),
    building_code VARCHAR(20),
    room VARCHAR(20),
    class_type VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_section_meetings_section_id
    ON section_meetings(section_id);

DELETE FROM section_meetings AS duplicate
USING section_meetings AS original
WHERE duplicate.id > original.id
  AND duplicate.section_id = original.section_id
  AND duplicate.days IS NOT DISTINCT FROM original.days
  AND duplicate.start_time IS NOT DISTINCT FROM original.start_time
  AND duplicate.end_time IS NOT DISTINCT FROM original.end_time
  AND duplicate.building_code IS NOT DISTINCT FROM original.building_code
  AND duplicate.room IS NOT DISTINCT FROM original.room
  AND duplicate.class_type IS NOT DISTINCT FROM original.class_type;

CREATE UNIQUE INDEX IF NOT EXISTS idx_section_meetings_identity
    ON section_meetings(
        section_id,
        days,
        start_time,
        end_time,
        building_code,
        room,
        class_type
    );
"""


def _safe_int(value):
    value_str = str(value).strip() if value is not None else ""
    return int(value_str) if value_str.isdigit() else 0


def _normalize_meeting_tuple(meeting):
    return (
        str(meeting.get("days") or "").strip(),
        str(meeting.get("start_time") or "").strip(),
        str(meeting.get("end_time") or "").strip(),
        str(meeting.get("building_code") or "").strip(),
        str(meeting.get("room") or "").strip(),
        str(meeting.get("class_type") or "").strip(),
    )


def get_connection():
    """Establish and return a database connection."""
    return psycopg2.connect(**get_db_connect_params())


def _department_code(course_code):
    normalized = str(course_code or "").strip().upper()
    match = DEPT_CODE_RE.match(normalized)
    if match is None:
        raise ValueError(f"Cannot parse department from course code {course_code!r}")
    return match.group("department")


def _create_schema(cursor):
    cursor.execute(SCHEMA_SQL)


def _upsert_system_data(cursor, available_departments, semester_code):
    cursor.execute("UPDATE semesters SET is_active = FALSE")
    cursor.execute(
        """
        INSERT INTO semesters (semester_code, name, is_active)
        VALUES (%s, %s, TRUE)
        ON CONFLICT (semester_code) DO UPDATE SET
            name = EXCLUDED.name,
            is_active = TRUE;
        """,
        (semester_code, f"Semester {semester_code}"),
    )
    execute_batch(
        cursor,
        """
        INSERT INTO departments (department_code, name)
        VALUES (%s, %s)
        ON CONFLICT (department_code) DO UPDATE SET name = EXCLUDED.name;
        """,
        list(available_departments),
        page_size=250,
    )


def _upsert_courses(cursor, courses):
    course_rows = []
    for course in courses:
        course_rows.append(
            (
                course["course_code"],
                _department_code(course["course_code"]),
                course.get("course_name", ""),
                course.get("course_credits", ""),
                course.get("description", ""),
                course.get("grading_options", []),
                course.get("gened_codes", []),
                json.dumps(course.get("attributes", {})),
            )
        )

    execute_batch(
        cursor,
        """
        INSERT INTO courses (
            course_code, department_code, title, credits,
            description, grading_options, gened_codes, attributes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (course_code) DO UPDATE SET
            department_code = EXCLUDED.department_code,
            title = EXCLUDED.title,
            credits = EXCLUDED.credits,
            description = EXCLUDED.description,
            grading_options = EXCLUDED.grading_options,
            gened_codes = EXCLUDED.gened_codes,
            attributes = EXCLUDED.attributes,
            last_updated = CURRENT_TIMESTAMP;
        """,
        course_rows,
        page_size=250,
    )


def _replace_sections(cursor, courses, semester_code):
    cursor.execute("DELETE FROM sections WHERE semester_code = %s", (semester_code,))

    section_rows = []
    meetings_by_section = {}
    for course in courses:
        course_code = course["course_code"]
        for section in course.get("sections", []):
            section_code = section["section_code"]
            section_key = (course_code, section_code)
            section_rows.append(
                (
                    course_code,
                    semester_code,
                    section_code,
                    section.get("instructors", []),
                    _safe_int(section.get("total_seats", "")),
                    _safe_int(section.get("open_seats", "")),
                    _safe_int(section.get("waitlist_count", "")),
                )
            )
            meetings_by_section[section_key] = sorted(
                {
                    _normalize_meeting_tuple(meeting)
                    for meeting in section.get("time_info", [])
                }
            )

    if not section_rows:
        return 0, 0

    section_rows = execute_values(
        cursor,
        """
        INSERT INTO sections (
            course_code, semester_code, section_code, instructors,
            total_seats, open_seats, waitlist
        ) VALUES %s
        RETURNING id, course_code, section_code;
        """,
        section_rows,
        page_size=250,
        fetch=True,
    )
    section_id_map = {
        (course_code, section_code): section_id
        for section_id, course_code, section_code in section_rows
    }

    meeting_rows = []
    for section_key, section_id in section_id_map.items():
        meeting_rows.extend(
            (section_id, *meeting) for meeting in meetings_by_section[section_key]
        )

    execute_batch(
        cursor,
        """
        INSERT INTO section_meetings (
            section_id, days, start_time, end_time,
            building_code, room, class_type
        ) VALUES (%s, %s, %s, %s, %s, %s, %s);
        """,
        meeting_rows,
        page_size=500,
    )

    return len(section_id_map), len(meeting_rows)


def sync_scraped_data(available_departments, semester_code, courses):
    """Publish one complete scrape as one transaction."""
    if not courses:
        raise ValueError("Cannot publish an empty course collection")

    started_at = time.time()
    conn = get_connection()
    try:
        conn.autocommit = False
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT pg_try_advisory_xact_lock(%s)",
                (SCRAPER_ADVISORY_LOCK_KEY,),
            )
            lock_row = cursor.fetchone()
            if not lock_row or not lock_row[0]:
                raise RuntimeError("Another scraper is already publishing data")

            _create_schema(cursor)
            _upsert_system_data(cursor, available_departments, semester_code)
            _upsert_courses(cursor, courses)
            section_count, meeting_count = _replace_sections(
                cursor, courses, semester_code
            )

        conn.commit()
        print(
            "SCRAPE_COUNTS "
            f"courses={len(courses)} "
            f"sections={section_count} "
            f"meetings={meeting_count}"
        )
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    print(
        f"Successfully published {len(courses)} courses into the database "
        f"in {time.time() - started_at:.2f}s."
    )
