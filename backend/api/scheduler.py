import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

import requests

from api.database import get_db_connection

P_TERP_PROF_URL = "https://planetterp.com/api/v1/professor"
P_TERP_PROF_GRADES_CLASS_URL = "https://planetterp.com/api/v1/grades"


def _parse_time_to_minutes(t: str):
    """Parse 12h (with am/pm) or 24h time string to minutes since midnight.
    Returns None on parse failure or empty input.
    Examples accepted: '10:00am', '10:00 am', '12:50pm', '13:00', '09:05'
    """
    if not t:
        return None
    s = t.strip().lower().replace(".", "")
    # remove interior space before am/pm if present
    if s.endswith(" am") or s.endswith(" pm"):
        s = s.replace(" ", "")
    try:
        if s.endswith("am") or s.endswith("pm"):
            dt = datetime.strptime(s, "%I:%M%p")
        else:
            dt = datetime.strptime(s, "%H:%M")
        return dt.hour * 60 + dt.minute
    except Exception:
        return None


def _normalize_day_token(day: str) -> Optional[str]:
    if not day:
        return None

    normalized = day.strip().lower()
    mapping = {
        "m": "M",
        "mon": "M",
        "monday": "M",
        "t": "T",
        "tu": "T",
        "tue": "T",
        "tues": "T",
        "tuesday": "T",
        "w": "W",
        "wed": "W",
        "wednesday": "W",
        "r": "R",
        "th": "R",
        "thu": "R",
        "thur": "R",
        "thurs": "R",
        "thursday": "R",
        "f": "F",
        "fri": "F",
        "friday": "F",
        "s": "S",
        "sat": "S",
        "saturday": "S",
        "u": "U",
        "sun": "U",
        "sunday": "U",
    }
    return mapping.get(normalized)


def _parse_days_to_tokens(days: str) -> Set[str]:
    if not days:
        return set()

    s = days.strip().lower().replace(" ", "")
    tokens = []
    i = 0
    while i < len(s):
        if s.startswith("th", i):
            tokens.append("R")
            i += 2
            continue
        if s.startswith("tu", i):
            tokens.append("T")
            i += 2
            continue
        if s.startswith("su", i):
            tokens.append("U")
            i += 2
            continue
        if s.startswith("sa", i):
            tokens.append("S")
            i += 2
            continue

        mapped = _normalize_day_token(s[i])
        if mapped:
            tokens.append(mapped)
        i += 1

    return set(tokens)


def time_overlap(start_db, end_db, start_24, end_24):
    """Return True if class times overlap, False otherwise."""
    s1 = _parse_time_to_minutes(start_db)
    e1 = _parse_time_to_minutes(end_db)
    s2 = _parse_time_to_minutes(start_24)
    e2 = _parse_time_to_minutes(end_24)
    # compare start/end times
    if s1 is None or e1 is None or s2 is None or e2 is None:
        raise ValueError("Invalid time format provided.")
    if s1 == s2:
        return True
    if s1 < s2:
        return e1 > s2
    else:
        return e2 > s1


def _get_course_sections_from_db(cursor, course_code: str, semester: str) -> List[Dict]:
    cursor.execute(
        """
        SELECT id, section_code, instructors, total_seats, open_seats, waitlist
        FROM sections
        WHERE course_code = %s AND semester_code = %s
        ORDER BY section_code ASC
    """,
        (course_code, semester),
    )
    sections = cursor.fetchall()

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

    return sections


def _parse_min_credits(credits_value: Optional[str]) -> int:
    if credits_value is None:
        return 0

    credits_text = str(credits_value).strip()
    if not credits_text:
        return 0

    match = re.match(r"^(\d+)(?:\s*-\s*(\d+))?$", credits_text)
    if not match:
        return 0

    first = int(match.group(1))
    second = match.group(2)
    if second is None:
        return first
    return min(first, int(second))


def _get_course_min_credits_map(course_codes: Sequence[str]) -> Dict[str, int]:
    if not course_codes:
        return {}

    with get_db_connection() as cursor:
        cursor.execute(
            """
            SELECT course_code, credits
            FROM courses
            WHERE course_code = ANY(%s)
        """,
            (list(course_codes),),
        )
        rows = cursor.fetchall()

    return {row["course_code"]: _parse_min_credits(row.get("credits")) for row in rows}


def _sections_conflict(section_a: Dict, section_b: Dict) -> bool:
    for time1 in section_a.get("meetings", []):
        days1 = _parse_days_to_tokens(time1.get("days", ""))
        if not days1:
            continue

        start1 = time1.get("start_time", "")
        end1 = time1.get("end_time", "")
        if not start1 or not end1:
            continue

        for time2 in section_b.get("meetings", []):
            days2 = _parse_days_to_tokens(time2.get("days", ""))
            if not days2:
                continue

            start2 = time2.get("start_time", "")
            end2 = time2.get("end_time", "")
            if not start2 or not end2:
                continue

            if days1.intersection(days2) and time_overlap(start1, end1, start2, end2):
                return True
    return False


def _schedule_signature(schedule: Dict[str, Dict]) -> Tuple[Tuple[str, str], ...]:
    return tuple(
        sorted(
            (course_code, str(section.get("section_code", "")))
            for course_code, section in schedule.items()
        )
    )


def _expand_schedule_with_optional_courses(
    base_schedule: Dict[str, Dict],
    optional_course_codes: Sequence[str],
    optional_domains: Dict[str, List[Dict]],
    course_min_credits: Dict[str, int],
    max_credits: Optional[int],
) -> List[Dict[str, Dict]]:
    base = dict(base_schedule)
    base_credits = sum(course_min_credits.get(course_code, 0) for course_code in base)

    if max_credits is not None and base_credits > max_credits:
        return []

    expanded: List[Dict[str, Dict]] = []

    def _dfs_optional(idx: int, current: Dict[str, Dict], current_credits: int):
        if idx >= len(optional_course_codes):
            expanded.append(current.copy())
            return

        course_code = optional_course_codes[idx]
        sections = optional_domains.get(course_code, [])

        # Option 1: skip this optional course.
        _dfs_optional(idx + 1, current, current_credits)

        # Option 2: include one viable section from this optional course.
        course_credits = course_min_credits.get(course_code, 0)
        for section in sections:
            if (
                max_credits is not None
                and current_credits + course_credits > max_credits
            ):
                continue

            if any(
                _sections_conflict(section, existing) for existing in current.values()
            ):
                continue

            current[course_code] = section
            _dfs_optional(idx + 1, current, current_credits + course_credits)
            del current[course_code]

    _dfs_optional(0, base, base_credits)
    return expanded


def preprocess_restrictions(
    required_courses,
    excluded_profs,
    time_constraints,
    semester,
    only_open_seats: bool = True,
):
    VARIABLES = required_courses
    DOMAINS = {}
    excluded_set = {p.strip().lower() for p in (excluded_profs or []) if p.strip()}

    with get_db_connection() as cursor:
        for course_code in required_courses:
            sections = _get_course_sections_from_db(cursor, course_code, semester)

            filtered_sections = []

            for section in sections:
                if "FC" in section.get("section_code", ""):
                    continue  # TODO: handle freshman connection sections specially later, must be all FC or no FC
                # excluded professors
                section_instructors = section.get("instructors", [])
                if excluded_set and any(
                    prof and prof.strip().lower() in excluded_set
                    for prof in section_instructors
                ):
                    continue

                # time constraints
                if time_constraints:
                    conflict = False
                    for section_time in section.get("meetings", []):
                        days = _parse_days_to_tokens(section_time.get("days", ""))
                        start_time = section_time.get("start_time")
                        end_time = section_time.get("end_time")
                        if not days or not start_time or not end_time:
                            continue

                        for tc_day, tc_start, tc_end in time_constraints:
                            normalized_day = _normalize_day_token(tc_day)
                            if normalized_day is None:
                                continue

                            # mark conflict if the section occurs on the constrained day
                            # and its time overlaps the restricted interval at all
                            if normalized_day in days and time_overlap(
                                start_time, end_time, tc_start, tc_end
                            ):
                                conflict = True
                                break
                        if conflict:
                            break
                    if conflict:
                        continue
                # if requested, only include sections with at least one open seat
                if only_open_seats and section.get("open_seats", 0) < 1:
                    continue

                filtered_sections.append(section)

            DOMAINS[course_code] = filtered_sections
    return VARIABLES, DOMAINS


def backtrack_schedules(variables, domains, assignment=None):
    if assignment is None:
        assignment = {}

    if len(assignment) == len(variables):
        return [assignment.copy()]

    unassigned_vars = [v for v in variables if v not in assignment]
    first_var = unassigned_vars[0]
    schedules = []

    for value in domains[first_var]:
        # Check if this new section conflicts with existing assignments
        conflict = False
        for assigned_var in assignment:
            assigned_section = assignment[assigned_var]
            # check time conflicts between value and assigned_section
            for time1 in value.get("meetings", []):
                days1 = _parse_days_to_tokens(time1.get("days", ""))
                if days1 == set():
                    continue
                start1 = time1.get("start_time", "")
                if not start1:
                    continue
                end1 = time1.get("end_time", "")
                if not end1:
                    continue
                for time2 in assigned_section.get("meetings", []):
                    days2 = _parse_days_to_tokens(time2.get("days", ""))
                    if days2 == set():
                        continue
                    start2 = time2.get("start_time", "")
                    if not start2:
                        continue
                    end2 = time2.get("end_time", "")
                    if not end2:
                        continue
                    # check if days overlap and times overlap
                    if days1.intersection(days2):
                        if time_overlap(start1, end1, start2, end2):
                            conflict = True
                            break
                if conflict:
                    break
            if conflict:
                break

        if conflict:
            continue  # skip this value, try next section

        # No conflict, assign and recurse
        assignment[first_var] = value
        result = backtrack_schedules(variables, domains, assignment)
        schedules.extend(result)
        del assignment[first_var]

    # Deduplicate schedules
    seen = set()
    unique_schedules = []
    for sched in schedules:
        sched_tuple = tuple(
            (course, section["section_code"]) for course, section in sched.items()
        )
        if sched_tuple not in seen:
            seen.add(sched_tuple)
            unique_schedules.append(sched)
    return unique_schedules


def get_prof_ratings(professors, excluded_profs):
    needed_profs = set(professors) - set(excluded_profs or [])
    prof_ratings = {}
    for prof in needed_profs:
        try:
            response = requests.get(
                P_TERP_PROF_URL + f"?name={prof.replace(' ', '%20')}",
            )
            data = response.json()
            if "error" in data:
                prof_ratings[prof] = 0
            elif data["average_rating"] is None:
                prof_ratings[prof] = 0  # default to 0
            else:
                prof_ratings[prof] = data["average_rating"]
        except Exception as e:
            print(f"Error fetching rating for professor {prof}: {e}")
            prof_ratings[prof] = 0
    prof_ratings["Instructor: TBA"] = 0  # assign average rating for TBA instructors
    return prof_ratings


def get_prof_grades_for_course(professor, course_code):
    """Fetch grade distribution for a professor-course pair from PlanetTerp API.

    Returns:
        dict: Grade counts by letter grade, or None if data unavailable
    """
    try:
        response = requests.get(
            P_TERP_PROF_GRADES_CLASS_URL
            + f"?professor={professor.replace(' ', '%20')}&course={course_code}"
        )
        if response.status_code == 400:
            return None

        grades_data = response.json()

        # Aggregate grades across all semesters for this prof-course pair
        possible_grades = [
            "A+",
            "A",
            "A-",
            "B+",
            "B",
            "B-",
            "C+",
            "C",
            "C-",
            "D+",
            "D",
            "D-",
            "F",
            "W",
            "Other",
        ]
        grade_counts = {grade: 0 for grade in possible_grades}

        for semester_data in grades_data:
            # Verify correct course and professor
            if semester_data.get("course") != course_code:
                continue
            if semester_data.get("professor") != professor:
                continue

            for grade in possible_grades:
                if grade in semester_data:
                    grade_counts[grade] += semester_data[grade]

        return grade_counts
    except Exception as e:
        print(f"Error fetching grades for {professor} in {course_code}: {e}")
        return None


def calculate_weighted_gpa_for_section(course_code, professors):
    """Calculate weighted average GPA for a section with one or more professors.

    For co-taught sections, weights each professor's GPA by their grade count.

    Args:
        course_code: Course identifier (e.g., "CMSC131")
        professors: List of professor names teaching this section

    Returns:
        float or None: Weighted average GPA rounded to 2 decimals, or None if no data
    """
    if not professors:
        return None

    grade_to_points = {
        "A+": 4.0,
        "A": 4.0,
        "A-": 3.7,
        "B+": 3.3,
        "B": 3.0,
        "B-": 2.7,
        "C+": 2.3,
        "C": 2.0,
        "C-": 1.7,
        "D+": 1.3,
        "D": 1.0,
        "D-": 0.7,
        "F": 0.0,
    }

    total_weighted_sum = 0
    total_grade_count = 0

    for professor in professors:
        grade_counts = get_prof_grades_for_course(professor, course_code)
        if grade_counts is None:
            continue

        # Calculate GPA for this professor in this course
        weighted_sum = sum(
            grade_counts[grade] * points
            for grade, points in grade_to_points.items()
            if grade in grade_counts
        )
        # Don't count W (withdraw) or Other in GPA calculation
        prof_total = sum(
            grade_counts[grade] for grade in grade_counts if grade not in ["W", "Other"]
        )

        if prof_total > 0:
            total_weighted_sum += weighted_sum
            total_grade_count += prof_total

    if total_grade_count > 0:
        return round(total_weighted_sum / total_grade_count, 2)

    return None


def build_schedules(
    required_courses: Sequence[str],
    semester: str,
    excluded_profs: Optional[Sequence[str]] = None,
    time_constraints: Optional[Sequence[Tuple[str, str, str]]] = None,
    max_schedules: int = 50,
    optional_courses: Optional[Sequence[str]] = None,
    max_credits: Optional[int] = None,
    min_credits: Optional[int] = None,
    only_open_seats: bool = True,
):
    VARIABLES, DOMAINS = preprocess_restrictions(
        required_courses=required_courses,
        excluded_profs=excluded_profs,
        time_constraints=time_constraints,
        semester=semester,
        only_open_seats=only_open_seats,
    )

    normalized_optional = []
    required_set = set(required_courses)
    for course_code in optional_courses or []:
        if course_code and course_code not in required_set:
            normalized_optional.append(course_code)

    _, OPTIONAL_DOMAINS = preprocess_restrictions(
        required_courses=normalized_optional,
        excluded_profs=excluded_profs,
        time_constraints=time_constraints,
        semester=semester,
        only_open_seats=only_open_seats,
    )

    ALL_DOMAINS = {**DOMAINS, **OPTIONAL_DOMAINS}

    # If any required course has no viable sections, no schedules are possible.
    if any(len(DOMAINS.get(course, [])) == 0 for course in required_courses):
        return []

    # Collect all professors from all sections
    full_profs = []
    for course_name, domain in ALL_DOMAINS.items():
        for section in domain:
            profs = section.get("instructors", [])
            full_profs.extend(profs)

    # Cache for professor-course GPA calculations to avoid redundant API calls
    gpa_cache = {}

    # Pre-calculate GPA for each unique professor-course combination
    for course_name, domain in ALL_DOMAINS.items():
        # Get unique professor combinations for this course
        prof_combos = set()
        for section in domain:
            profs = tuple(sorted(section.get("instructors", [])))
            if profs:
                prof_combos.add(profs)

        # Calculate GPA for each unique combination
        for prof_combo in prof_combos:
            cache_key = (course_name, prof_combo)
            if cache_key not in gpa_cache:
                gpa_cache[cache_key] = calculate_weighted_gpa_for_section(
                    course_name, list(prof_combo)
                )

    # Add GPA data to each section in the domains
    for course_name, domain in ALL_DOMAINS.items():
        for section in domain:
            profs = tuple(sorted(section.get("instructors", [])))
            cache_key = (course_name, profs)
            section["avg_prof_gpa_in_class"] = gpa_cache.get(cache_key)

    # Get professor ratings
    prof_ratings = get_prof_ratings(full_profs, excluded_profs)

    # Generate base schedules for required courses only.
    required_schedules = backtrack_schedules(VARIABLES, DOMAINS)

    course_min_credits = _get_course_min_credits_map(
        list(required_courses) + normalized_optional
    )

    # Expand each required-only schedule by optionally including extra courses.
    expanded_schedules: List[Dict[str, Dict]] = []
    for base_schedule in required_schedules:
        if normalized_optional:
            expanded_schedules.extend(
                _expand_schedule_with_optional_courses(
                    base_schedule=base_schedule,
                    optional_course_codes=normalized_optional,
                    optional_domains=OPTIONAL_DOMAINS,
                    course_min_credits=course_min_credits,
                    max_credits=max_credits,
                )
            )
        else:
            expanded_schedules.append(base_schedule.copy())

    # Dedupe expanded schedules across base schedules.
    seen = set()
    unique_schedules = []
    for schedule in expanded_schedules:
        signature = _schedule_signature(schedule)
        if signature in seen:
            continue
        seen.add(signature)
        unique_schedules.append(schedule)

    schedule_records = []
    for unique_schedule in unique_schedules:
        total_credits = sum(
            course_min_credits.get(course_code, 0) for course_code in unique_schedule
        )

        # Defensive filter in case any schedule slipped past expansion checks.
        if max_credits is not None and total_credits > max_credits:
            continue
        if min_credits is not None and total_credits < min_credits:
            continue

        avg_schedule_prof_rating = 0.0
        total_instructors = 0
        for section in unique_schedule.values():
            instructors = section.get("instructors", [])
            for instructor in instructors:
                try:
                    avg_schedule_prof_rating += prof_ratings.get(instructor, 0)
                    total_instructors += 1
                except Exception as e:
                    print(f"Error adding rating for professor {instructor}: {e}")
                    continue

        if total_instructors > 0:
            avg_schedule_prof_rating = round(
                avg_schedule_prof_rating / total_instructors,
                2,
            )
        # else:
        #     avg_schedule_prof_rating = None

        included_optional_courses = sorted(
            [
                course_code
                for course_code in normalized_optional
                if course_code in unique_schedule
            ]
        )

        schedule_records.append(
            {
                "schedule": unique_schedule,
                "average_professor_rating": avg_schedule_prof_rating,
                "total_credits": total_credits,
                "included_optional_courses": included_optional_courses,
            }
        )

    schedule_records.sort(
        key=lambda record: (
            record["total_credits"],
            record["average_professor_rating"]
            if record["average_professor_rating"] is not None
            else -1,
        ),
        reverse=True,
    )

    api_schedules = []
    for record in schedule_records[:max_schedules]:
        record_schedule: Dict[str, Dict[Any, Any]] = record["schedule"]
        sections = []
        for course_code, section in sorted(
            record_schedule.items(), key=lambda item: item[0]
        ):
            section_payload = {
                "course_code": course_code,
                "section_code": section.get("section_code"),
                "instructors": section.get("instructors", []),
                "total_seats": section.get("total_seats", 0),
                "open_seats": section.get("open_seats", 0),
                "waitlist": section.get("waitlist", 0),
                "meetings": section.get("meetings", []),
                "avg_prof_gpa_in_class": section.get("avg_prof_gpa_in_class"),
            }
            sections.append(section_payload)

        api_schedules.append(
            {
                "sections": sections,
                "average_professor_rating": record["average_professor_rating"],
                "total_credits": record["total_credits"],
                "included_optional_courses": record["included_optional_courses"],
            }
        )

    return api_schedules
