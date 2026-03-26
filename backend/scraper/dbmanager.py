import getpass
import json

import psycopg2
from psycopg2.extras import execute_batch

DB_CREDENTIALS = {
    "dbname": "class_api",
    "user": getpass.getuser(),  # Automatically gets your Mac username!
    "password": "",  # Leave blank for local Homebrew installs
    "host": "localhost",
    "port": "5432",
}


def get_connection():
    """Establishes and returns a connection to the database."""
    return psycopg2.connect(**DB_CREDENTIALS)


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
    with get_connection() as conn:
        with conn.cursor() as cursor:
            for course in all_course_info:
                # Extract department code from the first 4 letters of course code (e.g., 'AAAS100' -> 'AAAS')
                import re

                match = re.match(r"([A-Z]{4})", course["course_code"])
                dept_code = match.group(1) if match else None

                # 1. Upsert the Course (Catalog)
                cursor.execute(
                    """
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
                """,
                    (
                        course["course_code"],
                        dept_code,
                        course.get("course_name", ""),
                        course.get("course_credits", ""),
                        course.get("description", ""),
                        course.get("grading_options", []),
                        course.get("gened_codes", []),
                        json.dumps(
                            course.get("attributes", {})
                        ),  # Convert dict to JSON string!
                    ),
                )

                # 2. Process Sections for this course
                for section in course.get("sections", []):
                    # Handle empty strings that should be integers
                    total_seats = (
                        int(section["total_seats"])
                        if section.get("total_seats", "").isdigit()
                        else 0
                    )
                    open_seats = (
                        int(section["open_seats"])
                        if section.get("open_seats", "").isdigit()
                        else 0
                    )
                    waitlist = (
                        int(section["waitlist_count"])
                        if section.get("waitlist_count", "").isdigit()
                        else 0
                    )

                    # 3. Upsert the Section (This is the hourly update magic!)
                    # We use RETURNING id so we know where to attach the meeting times.
                    cursor.execute(
                        """
                        INSERT INTO sections (
                            course_code, semester_code, section_code, instructors, 
                            total_seats, open_seats, waitlist
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (course_code, semester_code, section_code) DO UPDATE SET
                            instructors = EXCLUDED.instructors,
                            total_seats = EXCLUDED.total_seats,
                            open_seats = EXCLUDED.open_seats,
                            waitlist = EXCLUDED.waitlist,
                            last_updated = CURRENT_TIMESTAMP
                        RETURNING id;
                    """,
                        (
                            course["course_code"],
                            curr_sem_code,
                            section["section_code"],
                            section.get("instructors", []),
                            total_seats,
                            open_seats,
                            waitlist,
                        ),
                    )

                    section_id = cursor.fetchone()[0]

                    # 4. Handle Meetings
                    # Easiest update strategy: Delete old meetings, insert new ones.
                    cursor.execute(
                        "DELETE FROM section_meetings WHERE section_id = %s",
                        (section_id,),
                    )

                    meeting_data = []
                    for meeting in section.get("time_info", []):
                        meeting_data.append(
                            (
                                section_id,
                                meeting.get("days"),
                                meeting.get("start_time"),
                                meeting.get("end_time"),
                                meeting.get("building_code"),
                                meeting.get("room"),
                                meeting.get("class_type"),
                            )
                        )

                    if meeting_data:
                        execute_batch(
                            cursor,
                            """
                            INSERT INTO section_meetings (
                                section_id, days, start_time, end_time, 
                                building_code, room, class_type
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s);
                        """,
                            meeting_data,
                        )

            print(
                f"Successfully processed {len(all_course_info)} courses into the database."
            )
