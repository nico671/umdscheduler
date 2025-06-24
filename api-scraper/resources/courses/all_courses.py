import bs4 as BeautifulSoup
import requests
from flask_restful import Resource, reqparse

from resources.courses.utils.all_courses_utils import (
    SINGLE_DEPT_COURSES,
    int_or_string,
    validate_geneds,
    validate_min_credits,
    validate_semester,
)
from resources.departments import _depts_fetcher


def get_all_courses(
    semester, min_credits, min_credits_comparator, dept_id=None, gen_eds=None
):
    if dept_id:
        dept_code_list = [dept_id]
    else:
        all_depts = _depts_fetcher()
        dept_code_list = []
        for dept in all_depts:
            for key in dept:
                dept_code_list.append(key)
    all_courses = []

    for dept in dept_code_list:
        url = SINGLE_DEPT_COURSES.format(semester=semester, dept_code=dept)
        dept_courses = []
        resp = requests.get(url)
        if resp.status_code != 200:
            raise ValueError(
                f"Failed to fetch courses for semester {semester} and department {dept}. Status code: {resp.status_code}"
            )
        soup = BeautifulSoup.BeautifulSoup(resp.text, "html.parser")
        courses_container = soup.find("div", {"id": "courses-page"})
        dept_info = courses_container.find("div", {"class": "course-prefix-info"})
        dept_code = dept_info.find("span", {"class": "course-prefix-abbr"}).text.strip()
        dept_name = dept_info.find("span", {"class": "course-prefix-name"}).text.strip()
        courses_list = courses_container.find("div", {"class": "courses-container"})
        for course in courses_list.find_all("div", {"class": "course"}):
            # basic info
            course_code = course.find("div", {"class": "course-id"}).text.strip()
            course_name = course.find("span", {"class": "course-title"}).text.strip()
            course_credits = course.find(
                "span", {"class": "course-min-credits"}
            ).text.strip()

            if min_credits_comparator:
                if (
                    min_credits_comparator == "eq"
                    and int(course_credits) != min_credits
                ):
                    continue
                elif (
                    min_credits_comparator == "lt"
                    and int(course_credits) >= min_credits
                ):
                    continue
                elif (
                    min_credits_comparator == "gt"
                    and int(course_credits) <= min_credits
                ):
                    continue
                elif (
                    min_credits_comparator == "geq"
                    and int(course_credits) < min_credits
                ):
                    continue
                elif (
                    min_credits_comparator == "leq"
                    and int(course_credits) > min_credits
                ):
                    continue
            else:
                if int(course_credits) < min_credits:
                    continue

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
            else:
                print("No geneds found for this course.")
            if gen_eds:
                if not any(gened in gened_list for gened in gen_eds):
                    continue
            # extra info (description, restrictions, prerequisites, etc.)
            extra_info = course.find_all("div", {"class": "approved-course-text"})
            course_description = ""
            coreqs = ""  # done
            prereqs = ""  # done
            formerly = ""  # done
            restrictions = ""  # done
            additional_info = []
            crosslisted_as = ""
            credit_granted_for = ""  # done
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
                            c
                            for c in div.find_all(recursive=False)
                            if c.name != "strong"
                        ]
                        if other_tag_children:
                            continue
                        sub_text = div.text.strip()
                        if "Prerequisite" in sub_text:
                            # print("Found prerequisites", sub_text)
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
            dept_courses.append(curr_course)
        all_courses.extend(dept_courses)
    return all_courses


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
            help='min_credits parameter must be in the form "<number>|<comparator>"',
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
