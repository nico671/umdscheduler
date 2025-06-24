CREATE TABLE departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dept_code TEXT UNIQUE NOT NULL,
    dept_name TEXT NOT NULL
);

CREATE TABLE courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id TEXT NOT NULL,
    course_name TEXT NOT NULL,
    course_credits INTEGER,
    grading_method TEXT,
    description TEXT,
    prerequisites TEXT,
    corequisites TEXT,
    restrictions TEXT,
    formerly TEXT,
    crosslisted_as TEXT,
    credit_granted_for TEXT,
    dept_id INTEGER NOT NULL,
    FOREIGN KEY (dept_id) REFERENCES departments(id)
);

CREATE TABLE geneds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE course_geneds (
    course_id INTEGER,
    gened_id INTEGER,
    PRIMARY KEY (course_id, gened_id),
    FOREIGN KEY (course_id) REFERENCES courses(id),
    FOREIGN KEY (gened_id) REFERENCES geneds(id)
);

CREATE TABLE sections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER,
    section_id TEXT NOT NULL,
    total_seats INTEGER,
    open_seats INTEGER,
    waitlist_count INTEGER,
    FOREIGN KEY (course_id) REFERENCES courses(id)
);

CREATE TABLE section_instructors (
    section_id INTEGER,
    instructor_name TEXT,
    FOREIGN KEY (section_id) REFERENCES sections(id)
);

CREATE TABLE meeting_times (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    section_id INTEGER,
    meeting_days TEXT,
    start_time TEXT,
    end_time TEXT,
    building TEXT,
    class_type TEXT,
    FOREIGN KEY (section_id) REFERENCES sections(id)
);


