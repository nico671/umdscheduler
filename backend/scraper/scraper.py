import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter

from . import dbmanager

TESTUDO_HOME_URL = "https://app.testudo.umd.edu/soc/"
TESTUDO_DEPT_URL = "https://app.testudo.umd.edu/soc/{current_semester}/{dept_abbr}"
TESTUDO_SPEC_COURSE_URL = "https://app.testudo.umd.edu/soc/search?courseId={course_code}&sectionId=&termId={current_semester}&_openSectionsOnly=on&creditCompare=%3E%3D&credits=0.0&courseLevelFilter=ALL&instructor=&_facetoface=on&_blended=on&_online=on&courseStartCompare=&courseStartHour=&courseStartMin=&courseStartAM=&courseEndHour=&courseEndMin=&courseEndAM=&teachingCenter=ALL&_classDay1=on&_classDay2=on&_classDay3=on&_classDay4=on&_classDay5=on"

REQUEST_TIMEOUT_SECONDS = 20

MAX_WORKERS = 25
COURSE_CODE_RE = re.compile(r"^(?P<department>[A-Z]{4})(?P<number>\d{3,4}[A-Z]?)$")

_thread_local = threading.local()


class ScrapeError(RuntimeError):
    """Raised when Testudo data is incomplete or cannot be parsed."""


def _request(url, session=None):
    client = session or requests
    response = client.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response


def _parse_course_code(course_code):
    normalized = str(course_code or "").strip().upper()
    if COURSE_CODE_RE.fullmatch(normalized) is None:
        raise ScrapeError(
            f"Cannot parse course code discovered from Testudo: {course_code!r}"
        )
    return normalized


def _raise_worker_failures(kind, failures):
    if not failures:
        return
    sample = ", ".join(f"{identifier}: {error}" for identifier, error in failures[:3])
    raise ScrapeError(f"{len(failures)} {kind} worker failure(s); sample: {sample}")


def get_thread_session():
    if not hasattr(_thread_local, "session"):
        session = requests.Session()
        # Allow 20 concurrent connections to the same host
        adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20)
        session.mount("https://", adapter)
        _thread_local.session = session
    return _thread_local.session


def scrape_all_available_semesters():
    resp = _request(TESTUDO_HOME_URL)
    soup = BeautifulSoup(resp.text, "lxml")

    semesters_select_elt = soup.find("select", {"id": "term-id-input"})
    semesters = []
    if semesters_select_elt is None:
        raise ScrapeError("Missing semester selector on the Testudo homepage")
    for option in semesters_select_elt.find_all("option"):
        sem_name = option.text.strip()
        sem_code = option["value"]
        semesters.append((sem_name, sem_code))
    if not semesters:
        raise ScrapeError("Semester selector on the Testudo homepage is empty")
    return semesters


def scrape_all_available_departments_for_current_semester():
    resp = _request(TESTUDO_HOME_URL)
    soup = BeautifulSoup(resp.text, "lxml")

    curr_sem_code = None
    semesters_select_elt = soup.find("select", {"id": "term-id-input"})
    if semesters_select_elt is None:
        raise ScrapeError("Missing semester selector on the Testudo homepage")
    for option in semesters_select_elt.find_all("option"):
        if "selected" in option.attrs:
            curr_sem_code = option["value"]
            print(option.text.strip(), curr_sem_code)

    if not curr_sem_code:
        raise ScrapeError("Missing current semester on the Testudo homepage")

    course_prefix_div = soup.find("div", {"id": "course-prefixes-page"})
    if course_prefix_div is None:
        raise ScrapeError("Missing department container on the Testudo homepage")
    dept_entries = course_prefix_div.find_all("div", {"class": "course-prefix row"})
    if not dept_entries:
        raise ScrapeError("Testudo returned an empty department list")
    available_depts = []
    for course_entry in dept_entries:
        dept_abbr_name = None
        dept_full_name = None
        for span in course_entry.find_all("span"):
            if "prefix-abbrev" == span["class"][0]:
                dept_abbr_name = span.text.strip()
            elif "prefix-name" == span["class"][0]:
                dept_full_name = span.text.strip()
        if dept_abbr_name and dept_full_name:
            available_depts.append((dept_abbr_name, dept_full_name))
        else:
            print(dept_abbr_name, dept_full_name)
    if not available_depts:
        raise ScrapeError("Testudo returned no usable departments")
    return available_depts, curr_sem_code


def scrape_all_courses_with_sections(course_codes, curr_sem_code):
    all_course_info = []
    failures = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(
                scrape_course_info_for_course_code_with_sections,
                course_code,
                curr_sem_code,
            ): course_code
            for course_code in course_codes
        }

        for future in as_completed(futures):
            course_code = futures[future]
            try:
                course_data = future.result()
                if course_data:
                    all_course_info.append(course_data)
                else:
                    failures.append((course_code, "no course data returned"))
            except Exception as e:
                failures.append((course_code, e))

    _raise_worker_failures("course", failures)
    if not all_course_info:
        raise ScrapeError("Testudo returned an empty course list")
    return all_course_info


def scrape_course_info_for_course_code_with_sections(course_code, curr_sem_code):
    course_code = _parse_course_code(course_code)
    print(f"Scraping {course_code}")
    session = get_thread_session()
    course_url = TESTUDO_SPEC_COURSE_URL.format(
        course_code=course_code, current_semester=curr_sem_code
    )
    course_resp = _request(course_url, session=session)
    course_page_soup = BeautifulSoup(course_resp.text, "lxml")

    course_div = course_page_soup.find("div", {"class": "course", "id": course_code})
    if course_div is None:
        raise ScrapeError(f"Course {course_code} is missing from Testudo response")

    course_info = {
        "course_code": course_code,
    }
    course_name = course_div.find("span", {"class": "course-title"})
    if course_name:
        course_info["course_name"] = course_name.text.strip()
    else:
        course_info["course_name"] = ""
        print(f"Course name not found for {course_code}")

    course_credits = course_div.find("span", {"class": "course-min-credits"})
    if course_credits:
        course_info["course_credits"] = course_credits.text.strip()
    else:
        course_info["course_credits"] = ""
        print(f"Course credits not found for {course_code}")

    grading_methods_span = course_div.find("span", {"class": "grading-method"})
    grading_options = (
        grading_methods_span.find("abbr")["title"].strip().split(", ")
        if grading_methods_span and grading_methods_span.find("abbr")
        else []
    )
    course_info["grading_options"] = grading_options

    gened_codes = []
    for gened_span in course_div.find_all("span", {"class": "course-subcategory"}):
        gened_codes.append(gened_span.text.strip())
    course_info["gened_codes"] = gened_codes
    course_info["attributes"] = {}
    course_info["description"] = ""

    description_and_extra_attrs_container = course_page_soup.find(
        "div", class_="approved-course-texts-container"
    ) or course_page_soup.find("div", class_="course-texts-container")

    if not description_and_extra_attrs_container:
        print(f"Description and extra attributes container not found for {course_code}")
    else:
        text_blocks = description_and_extra_attrs_container.find_all(
            "div", class_=["approved-course-text", "course-text"]
        )

        for block in text_blocks:
            strong_tags = block.find_all("strong")
            if strong_tags:
                for strong in strong_tags:
                    key = strong.get_text(strip=True).rstrip(":").strip()
                    value_parts = []

                    for sibling in strong.next_siblings:
                        if getattr(sibling, "name", None) == "strong":
                            break

                        if isinstance(sibling, str):
                            part = sibling.strip()
                        else:
                            part = sibling.get_text(" ", strip=True)

                        if part:
                            value_parts.append(part)

                    value = " ".join(value_parts).strip()
                    if value:
                        course_info["attributes"][key] = value
            else:
                text = block.get_text("\n", strip=True)
                if course_info["description"]:
                    course_info["description"] += "\n\n" + text
                else:
                    course_info["description"] = text
    sections_container = course_page_soup.find("div", class_="sections-container")
    section_data = []
    if not sections_container:
        if not course_page_soup.find("div", class_="individual-instruction-message"):
            print(f"Sections container not found for {course_code}")
        else:
            course_info["attributes"]["Individual Instruction Message"] = (
                course_page_soup.find(
                    "div", class_="individual-instruction-message"
                ).text.strip()
            )
    else:
        for section_div in sections_container.find_all("div", class_="section"):
            section_info = scrape_section_info_from_section_div(section_div)
            if section_info:
                section_data.append(section_info)
    course_info["sections"] = section_data
    return course_info


def scrape_section_info_from_section_div(section_div):
    section_data = {}

    section_code_span = section_div.find("span", class_="section-id")
    if not section_code_span:
        return None

    section_code = section_code_span.text.strip()
    section_data["section_code"] = section_code

    section_data["instructors"] = [
        instructor_span.text.strip()
        for instructor_span in section_div.find_all("span", class_="section-instructor")
    ]

    total_seats_span = section_div.find("span", class_="total-seats-count")
    section_data["total_seats"] = (
        total_seats_span.text.strip() if total_seats_span else ""
    )

    open_seats_span = section_div.find("span", class_="open-seats-count")
    section_data["open_seats"] = open_seats_span.text.strip() if open_seats_span else ""

    waitlist_span = section_div.find("span", class_="waitlist-count")
    section_data["waitlist_count"] = waitlist_span.text.strip() if waitlist_span else ""

    section_class_days_container = section_div.find(
        "div", class_="class-days-container"
    )

    # Keep each row as a separate meeting block (no overwrite)
    meeting_times = []
    if section_class_days_container:
        for row in section_class_days_container.find_all("div", class_="row"):
            meeting_info = {}

            section_days_span = row.find("span", class_="section-days")
            meeting_info["days"] = (
                section_days_span.text.strip() if section_days_span else ""
            )

            section_start_time_span = row.find("span", class_="class-start-time")
            meeting_info["start_time"] = (
                section_start_time_span.text.strip() if section_start_time_span else ""
            )

            section_end_time_span = row.find("span", class_="class-end-time")
            meeting_info["end_time"] = (
                section_end_time_span.text.strip() if section_end_time_span else ""
            )

            location_info_span = row.find("span", class_="class-building")
            if location_info_span:
                building_code_span = location_info_span.find(
                    "span", class_="building-code"
                )
                meeting_info["building_code"] = (
                    building_code_span.text.strip() if building_code_span else ""
                )

                room_span = location_info_span.find("span", class_="class-room")
                meeting_info["room"] = room_span.text.strip() if room_span else ""
            else:
                meeting_info["building_code"] = ""
                meeting_info["room"] = ""

            class_type_span = row.find("span", class_="class-type")
            meeting_info["class_type"] = (
                class_type_span.text.strip() if class_type_span else ""
            )

            meeting_times.append(meeting_info)

    section_data["time_info"] = meeting_times
    return section_data


def scrape_available_course_codes_for_all_depts(available_depts, curr_sem_code):
    # use thread pool to scrape all departments in parallel
    all_course_codes = set()
    failures = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(
                scrape_available_course_codes_for_dept,
                dept_code,
                dept_name,
                curr_sem_code,
            ): (dept_code, dept_name)
            for dept_code, dept_name in available_depts
        }

        for future in as_completed(futures):
            dept_code, dept_name = futures[future]
            try:
                dept_course_codes = future.result()
                all_course_codes.update(dept_course_codes)
            except Exception as e:
                failures.append((dept_code, e))
    _raise_worker_failures("department", failures)
    if not all_course_codes:
        raise ScrapeError("Testudo returned an empty course-code list")
    return all_course_codes


def scrape_available_course_codes_for_dept(dept_code, dept_name, curr_sem_code):
    dept_url = TESTUDO_DEPT_URL.format(
        current_semester=curr_sem_code, dept_abbr=dept_code
    )
    print(f"Scraping course codes for {dept_code} - {dept_name}")
    session = get_thread_session()
    dept_resp = _request(dept_url, session=session)
    soup = BeautifulSoup(dept_resp.text, "lxml")

    all_dept_course_codes = {
        _parse_course_code(course_div.get("id"))
        for course_div in soup.find_all("div", {"class": "course"})
        if course_div.get("id")
    }
    if not all_dept_course_codes:
        raise ScrapeError(f"Department {dept_code} returned an empty course-code list")
    return sorted(all_dept_course_codes)


def collect_scraped_data():
    available_depts, curr_sem_code = (
        scrape_all_available_departments_for_current_semester()
    )
    all_course_codes = scrape_available_course_codes_for_all_depts(
        available_depts, curr_sem_code
    )
    scraped_course_info = scrape_all_courses_with_sections(
        all_course_codes, curr_sem_code
    )
    return available_depts, curr_sem_code, scraped_course_info


def run_scrape():
    start_time = time.time()
    available_depts, curr_sem_code, scraped_course_info = collect_scraped_data()
    print(f"Scraped info for {len(scraped_course_info)} courses")

    print("Saving to database...")
    dbmanager.sync_scraped_data(
        available_depts,
        curr_sem_code,
        scraped_course_info,
    )
    print("Database sync complete!")

    end_time = time.time()
    print(f"Scraping completed in {end_time - start_time:.2f} seconds")


if __name__ == "__main__":
    run_scrape()
