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

COURSE_COMMIT_CHUNK_SIZE = 200
PROGRESS_EVERY = 100
DEPT_CODE_RE = re.compile(r"([A-Z]{4})")


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
    """Establishes and returns a connection to the database."""
    return psycopg2.connect(**get_db_connect_params())


def create_tables():
    """Creates the database schema if it doesn't exist."""
    schema_sql = """
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

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(schema_sql)
            print("Database tables verified/created successfully.")


def upsert_system_data(available_depts, curr_sem_code):
    """Inserts the Semesters and Departments (The foundational data)"""
    with get_connection() as conn:
        with conn.cursor() as cursor:
            # 1. Upsert the Semester
            # (We derive the name from the code for now, e.g., '202608' -> 'Fall 2026')
            sem_name = f"Semester {curr_sem_code}"
            cursor.execute(
                """
                INSERT INTO semesters (semester_code, name, is_active)
                VALUES (%s, %s, %s)
                ON CONFLICT (semester_code) DO NOTHING;
            """,
                (curr_sem_code, sem_name, True),
            )

            # 2. Upsert Departments
            dept_data = [(code, name) for code, name in available_depts]
            execute_batch(
                cursor,
                """
                INSERT INTO departments (department_code, name)
                VALUES (%s, %s)
                ON CONFLICT (department_code) DO UPDATE SET name = EXCLUDED.name;
            """,
                dept_data,
            )


def upsert_courses_and_sections(all_course_info, curr_sem_code):
    """Inserts/Updates the catalog and the live schedule"""
    if not all_course_info:
        print("No courses provided for upsert.")
        return

    total_courses = len(all_course_info)
    start_time = time.time()

    course_upsert_sql = """
        INSERT INTO courses (
            course_code, department_code, title, credits,
            description, grading_options, gened_codes, attributes
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (course_code) DO UPDATE SET
            title = EXCLUDED.title,
            credits = EXCLUDED.credits,
            description = EXCLUDED.description,
            attributes = EXCLUDED.attributes,
            last_updated = CURRENT_TIMESTAMP;
    """

    section_upsert_sql = """
        INSERT INTO sections (
            course_code, semester_code, section_code, instructors,
            total_seats, open_seats, waitlist
        ) VALUES %s
        ON CONFLICT (course_code, semester_code, section_code) DO UPDATE SET
            instructors = EXCLUDED.instructors,
            total_seats = EXCLUDED.total_seats,
            open_seats = EXCLUDED.open_seats,
            waitlist = EXCLUDED.waitlist,
            last_updated = CURRENT_TIMESTAMP
        RETURNING id, course_code, section_code;
    """

    insert_meetings_sql = """
        INSERT INTO section_meetings (
            section_id, days, start_time, end_time,
            building_code, room, class_type
        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING;
    """

    processed_courses = 0
    processed_sections = 0
    meetings_inserted = 0
    unchanged_sections = 0

    with get_connection() as conn:
        conn.autocommit = False
        with conn.cursor() as cursor:
            for chunk_start in range(0, total_courses, COURSE_COMMIT_CHUNK_SIZE):
                course_chunk = all_course_info[
                    chunk_start : chunk_start + COURSE_COMMIT_CHUNK_SIZE
                ]

                course_batch = []
                section_batch = []
                meetings_by_section_key = {}

                for course in course_chunk:
                    match = DEPT_CODE_RE.match(course["course_code"])
                    dept_code = match.group(1) if match else None

                    course_batch.append(
                        (
                            course["course_code"],
                            dept_code,
                            course.get("course_name", ""),
                            course.get("course_credits", ""),
                            course.get("description", ""),
                            course.get("grading_options", []),
                            course.get("gened_codes", []),
                            json.dumps(course.get("attributes", {})),
                        )
                    )

                    for section in course.get("sections", []):
                        section_key = (course["course_code"], section["section_code"])

                        section_batch.append(
                            (
                                course["course_code"],
                                curr_sem_code,
                                section["section_code"],
                                section.get("instructors", []),
                                _safe_int(section.get("total_seats", "")),
                                _safe_int(section.get("open_seats", "")),
                                _safe_int(section.get("waitlist_count", "")),
                            )
                        )

                        normalized_meetings = sorted(
                            [
                                _normalize_meeting_tuple(m)
                                for m in section.get("time_info", [])
                            ]
                        )
                        meetings_by_section_key[section_key] = normalized_meetings

                if course_batch:
                    execute_batch(
                        cursor, course_upsert_sql, course_batch, page_size=250
                    )

                section_id_map = {}
                if section_batch:
                    section_rows = execute_values(
                        cursor,
                        section_upsert_sql,
                        section_batch,
                        page_size=250,
                        fetch=True,
                    )
                    section_id_map = {
                        (course_code, section_code): section_id
                        for section_id, course_code, section_code in section_rows
                    }

                changed_section_ids = []
                meetings_to_insert = []

                if section_id_map:
                    section_ids = list(section_id_map.values())
                    cursor.execute(
                        """
                        SELECT
                            section_id,
                            COALESCE(days, ''),
                            COALESCE(start_time, ''),
                            COALESCE(end_time, ''),
                            COALESCE(building_code, ''),
                            COALESCE(room, ''),
                            COALESCE(class_type, '')
                        FROM section_meetings
                        WHERE section_id = ANY(%s)
                        ORDER BY
                            section_id,
                            COALESCE(days, ''),
                            COALESCE(start_time, ''),
                            COALESCE(end_time, ''),
                            COALESCE(building_code, ''),
                            COALESCE(room, ''),
                            COALESCE(class_type, '');
                        """,
                        (section_ids,),
                    )

                    existing_by_section_id = {}
                    for row in cursor.fetchall():
                        section_id = row[0]
                        existing_by_section_id.setdefault(section_id, []).append(
                            row[1:]
                        )

                    for section_key, new_meetings in meetings_by_section_key.items():
                        section_id = section_id_map.get(section_key)
                        if not section_id:
                            continue

                        existing_meetings = existing_by_section_id.get(section_id, [])
                        if existing_meetings == new_meetings:
                            unchanged_sections += 1
                            continue

                        changed_section_ids.append(section_id)
                        for meeting in new_meetings:
                            meetings_to_insert.append((section_id, *meeting))

                if changed_section_ids:
                    cursor.execute(
                        "DELETE FROM section_meetings WHERE section_id = ANY(%s)",
                        (changed_section_ids,),
                    )

                if meetings_to_insert:
                    execute_batch(
                        cursor,
                        insert_meetings_sql,
                        meetings_to_insert,
                        page_size=500,
                    )

                conn.commit()

                processed_courses += len(course_chunk)
                processed_sections += len(section_batch)
                meetings_inserted += len(meetings_to_insert)

                elapsed = time.time() - start_time
                if (
                    processed_courses % PROGRESS_EVERY == 0
                    or processed_courses == total_courses
                ):
                    print(
                        "[DB] Progress "
                        f"{processed_courses}/{total_courses} courses | "
                        f"sections upserted: {processed_sections} | "
                        f"meetings inserted: {meetings_inserted} | "
                        f"sections unchanged: {unchanged_sections} | "
                        f"elapsed: {elapsed:.1f}s"
                    )

            total_elapsed = time.time() - start_time
            print(
                f"Successfully processed {total_courses} courses into the database "
                f"in {total_elapsed:.2f} seconds."
            )
