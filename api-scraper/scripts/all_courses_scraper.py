import os
import random
import sys
import time
from pathlib import Path

from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3

from common.utils import get_driver
from resources.courses.semesters import _semester_fetcher
from resources.courses.utils.all_courses_utils import (
    SINGLE_DEPT_COURSES,
)
from resources.departments import _depts_fetcher


def scraper_depts_and_semesters_fetcher():
    all_depts = _depts_fetcher()
    dept_code_list = []
    for dept in all_depts:
        for key in dept:
            dept_code_list.append(key)

    # select most recent of available semesters
    all_semesters = _semester_fetcher()
    max_sem = 0
    for sem in all_semesters:
        if int(sem["code"]) > max_sem:
            max_sem = int(sem["code"])
    return dept_code_list, max_sem


def scrape_department_with_retry(dept, semester, max_retries=3, base_delay=2):
    """
    Scrape courses for a specific department with retry logic.
    Args:
        dept (str): Department code to scrape.
        semester (int): Semester code to scrape.
        max_retries (int): Maximum number of retries on failure.
        base_delay (int): Base delay in seconds before retrying.
    Returns:
        tuple: (success: bool, courses_data: list or None, error_msg: str or None)
    """
    for attempt in range(max_retries + 1):
        try:
            with get_driver() as driver:
                driver.get(
                    SINGLE_DEPT_COURSES.format(semester=semester, dept_code=dept)
                )
                wait = WebDriverWait(driver, 15)

                button = wait.until(
                    EC.element_to_be_clickable((By.ID, "show-all-sections-button"))
                )
                button.click()
                wait.until(
                    EC.presence_of_element_located(
                        (By.CLASS_NAME, "sections-container")
                    )
                )

                soup = BeautifulSoup(driver.page_source, "html.parser")

                # Process the department data (extract this logic into a separate function)
                dept_data = process_department_data(soup, dept)
                return True, dept_data, None

        except TimeoutException:
            if attempt < max_retries:
                delay = base_delay * (2**attempt) + random.uniform(0, 1)
                print(
                    f"Timeout for {dept} (attempt {attempt + 1}/{max_retries + 1}). Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
            else:
                error_msg = f"Failed to scrape {dept} after {max_retries + 1} attempts due to timeouts"
                print(error_msg)
                return False, None, error_msg

        except Exception as e:
            error_msg = f"Unexpected error while processing {dept}: {e}"
            print(error_msg)
            return False, None, error_msg

    return False, None, "Unexpected end of retry loop"


def process_department_data(soup, dept_code):
    """Extract department data from BeautifulSoup object"""
    courses_container = soup.find("div", {"id": "courses-page"})
    dept_info = courses_container.find("div", {"class": "course-prefix-info"})
    dept_code = dept_info.find("span", {"class": "course-prefix-abbr"}).text.strip()
    dept_name = dept_info.find("span", {"class": "course-prefix-name"}).text.strip()

    dept_courses = []
    courses_list = courses_container.find("div", {"class": "courses-container"})

    for course in courses_list.find_all("div", {"class": "course"}):
        # ...existing code for processing individual courses...
        # (Keep all the existing course processing logic here)

        # basic info
        course_code = course.find("div", {"class": "course-id"}).text.strip()
        course_name = course.find("span", {"class": "course-title"}).text.strip()
        course_credits = course.find(
            "span", {"class": "course-min-credits"}
        ).text.strip()

        course_grading_method = course.find(
            "span", {"class": "grading-method"}
        ).text.strip()
        # geneds
        course_geneds_wrapper = course.find("span", {"class": "course-subcategory"})
        gened_list = []
        if course_geneds_wrapper is not None:
            for gened in course_geneds_wrapper.find_all("a"):
                gened_name = gened.text.strip()
                gened_list.append(gened_name)

        extra_info = course.find_all("div", {"class": "approved-course-text"})
        course_description = ""
        coreqs = ""
        prereqs = ""
        formerly = ""
        restrictions = ""
        additional_info = []
        crosslisted_as = ""
        credit_granted_for = ""

        for e in extra_info:
            if not e.find_all("div"):
                course_description = e.text.strip()
            else:
                for div in e.find_all("div"):
                    strong_children = [
                        c for c in div.find_all("strong", recursive=False)
                    ]
                    if not strong_children:
                        continue
                    other_tag_children = [
                        c for c in div.find_all(recursive=False) if c.name != "strong"
                    ]
                    if other_tag_children:
                        continue
                    sub_text = div.text.strip()
                    if "Prerequisite" in sub_text:
                        prereqs = sub_text
                    elif "Corequisite" in sub_text:
                        coreqs = sub_text
                    elif "Restriction" in sub_text:
                        restrictions = sub_text
                    elif "Credit only granted for" in sub_text:
                        credit_granted_for = sub_text
                    elif "Formerly" in sub_text:
                        formerly = sub_text
                    elif "Cross-listed with" in sub_text:
                        crosslisted_as = sub_text
                    else:
                        additional_info.append(sub_text)

        # process course sections
        sections_list = []
        delivery_methods = ["delivery-f2f", "delivery-online", "delivery-blended"]

        for delivery_method in delivery_methods:
            for section in course.find_all(
                "div", {"class": f"section {delivery_method}"}
            ):
                section_id = section.find("span", {"class": "section-id"}).text.strip()
                section_instructors = []
                for instructor in section.find_all(
                    "span", {"class": "section-instructor"}
                ):
                    instructor_name = instructor.text.strip()
                    section_instructors.append(instructor_name)
                section_total_seats = section.find(
                    "span", {"class": "total-seats-count"}
                ).text.strip()
                section_open_seats = section.find(
                    "span", {"class": "open-seats-count"}
                ).text.strip()
                section_waitlist_count = section.find(
                    "span", {"class": "waitlist-count"}
                ).text.strip()
                class_meetings_container = section.find(
                    "div", {"class": "class-days-container"}
                )
                meeting_times = []
                for meeting in class_meetings_container.find_all(
                    "div", {"class": "row"}
                ):
                    meeting_days = (
                        meeting.find("span", {"class": "section-days"}).text.strip()
                        if meeting.find("span", {"class": "section-days"})
                        else ""
                    )
                    meeting_start_time = (
                        meeting.find("span", {"class": "class-start-time"}).text.strip()
                        if meeting.find("span", {"class": "class-start-time"})
                        else ""
                    )
                    meeting_end_time = (
                        meeting.find("span", {"class": "class-end-time"}).text.strip()
                        if meeting.find("span", {"class": "class-end-time"})
                        else ""
                    )
                    building_info_container = meeting.find(
                        "span", {"class": "class-building"}
                    )
                    building = ""
                    if building_info_container and building_info_container.find(
                        "span", {"class": "building-code"}
                    ):
                        building += building_info_container.find(
                            "span", {"class": "building-code"}
                        ).text.strip()
                    if (
                        building_info_container
                        and building != ""
                        and building_info_container.find(
                            "span", {"class": "class-room"}
                        )
                    ):
                        building += f" {
                            building_info_container.find(
                                'span', {'class': 'class-room'}
                            ).text.strip()
                        }"
                    else:
                        building = "N/A"
                    class_type_container = meeting.find("span", {"class": "class-type"})
                    class_type = ""
                    if class_type_container:
                        class_type = class_type_container.text.strip()
                    meeting_times.append(
                        {
                            "meeting_days": meeting_days,
                            "meeting_start_time": meeting_start_time,
                            "meeting_end_time": meeting_end_time,
                            "building": building,
                            "class_type": class_type,
                        }
                    )
                sections_list.append(
                    {
                        "section_id": section_id,
                        "section_instructors": section_instructors,
                        "section_total_seats": section_total_seats,
                        "section_open_seats": section_open_seats,
                        "section_waitlist_count": section_waitlist_count,
                        "meeting_times": meeting_times,
                    }
                )

        curr_course = {}
        curr_course["course_id"] = course_code
        curr_course["course_name"] = course_name
        curr_course["course_credits"] = course_credits
        curr_course["course_grading_method"] = course_grading_method
        curr_course["dept_code"] = dept_code
        curr_course["dept_name"] = dept_name
        curr_course["geneds"] = gened_list
        curr_course["course_description"] = course_description
        curr_course["additional_info"] = {
            "prerequisites": prereqs,
            "corequisites": coreqs,
            "restrictions": restrictions,
            "formerly": formerly,
            "crosslisted_as": crosslisted_as,
            "credit_granted_for": credit_granted_for,
            "additional_info": additional_info,
        }
        curr_course["sections"] = sections_list
        dept_courses.append(curr_course)

    return {
        "dept_code": dept_code,
        "dept_name": dept_name,
        "courses": dept_courses,
    }


def scrape_all_courses():
    dept_code_list, semester = scraper_depts_and_semesters_fetcher()
    all_courses = []
    failed_departments = []

    for dept in dept_code_list:
        success, dept_data, error_msg = scrape_department_with_retry(dept, semester)

        if success:
            all_courses.append(dept_data)
            print(
                f"✓ Scraped {dept} department with {len(dept_data['courses'])} courses."
            )
        else:
            failed_departments.append((dept, error_msg))
            print(f"✗ Failed to scrape {dept}: {error_msg}")

    if failed_departments:
        print(f"\nFailed to scrape {len(failed_departments)} departments:")
        for dept, error in failed_departments:
            print(f"  - {dept}: {error}")

    return all_courses


def refresh_cache():
    data = scrape_all_courses()
    if not data:
        print("No data scraped. Exiting.")
        return

    project_root = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    conn = sqlite3.connect(project_root / "db" / "courses.sqlite")
    c = conn.cursor()
    c.execute("DELETE FROM meeting_times")
    c.execute("DELETE FROM section_instructors")
    c.execute("DELETE FROM sections")
    c.execute("DELETE FROM course_geneds")
    c.execute("DELETE FROM geneds")
    c.execute("DELETE FROM courses")
    c.execute("DELETE FROM departments")
    for dept in data:
        dept_code = dept["dept_code"]
        dept_name = dept["dept_name"]
        c.execute(
            "INSERT INTO departments (dept_code, dept_name) VALUES (?, ?)",
            (dept_code, dept_name),
        )
        dept_id = c.lastrowid

        for course in dept["courses"]:
            c.execute(
                """
                INSERT INTO courses (
                    course_id, course_name, course_credits, grading_method,
                    description, prerequisites, corequisites, restrictions,
                    formerly, crosslisted_as, credit_granted_for, dept_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    course["course_id"],
                    course["course_name"],
                    int(course["course_credits"]),
                    course["course_grading_method"],
                    course["course_description"],
                    course["additional_info"]["prerequisites"],
                    course["additional_info"]["corequisites"],
                    course["additional_info"]["restrictions"],
                    course["additional_info"]["formerly"],
                    course["additional_info"]["crosslisted_as"],
                    course["additional_info"]["credit_granted_for"],
                    dept_id,
                ),
            )
            course_db_id = c.lastrowid

            # Geneds
            for gened in course["geneds"]:
                c.execute("INSERT OR IGNORE INTO geneds (name) VALUES (?)", (gened,))
                c.execute("SELECT id FROM geneds WHERE name = ?", (gened,))
                gened_id = c.fetchone()[0]
                c.execute(
                    "INSERT INTO course_geneds (course_id, gened_id) VALUES (?, ?)",
                    (course_db_id, gened_id),
                )

            # Sections
            for section in course["sections"]:
                c.execute(
                    """
                    INSERT INTO sections (
                        course_id, section_id, total_seats, open_seats, waitlist_count
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        course_db_id,
                        section["section_id"],
                        int(section["section_total_seats"]),
                        int(section["section_open_seats"]),
                        int(section["section_waitlist_count"]),
                    ),
                )
                section_db_id = c.lastrowid

                for instructor in section["section_instructors"]:
                    c.execute(
                        "INSERT INTO section_instructors (section_id, instructor_name) VALUES (?, ?)",
                        (section_db_id, instructor),
                    )

                for mt in section["meeting_times"]:
                    c.execute(
                        """
                        INSERT INTO meeting_times (
                            section_id, meeting_days, start_time, end_time, building, class_type
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            section_db_id,
                            mt["meeting_days"],
                            mt["meeting_start_time"],
                            mt["meeting_end_time"],
                            mt["building"],
                            mt["class_type"],
                        ),
                    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    start = time.time()
    os.makedirs("db", exist_ok=True)
    refresh_cache()
    print("Cache updated.")
    end = time.time()
    print(f"Time taken: {end - start} seconds")
