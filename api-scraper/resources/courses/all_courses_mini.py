import requests
from bs4 import BeautifulSoup
from flask_restful import Resource, reqparse

from resources.courses.utils.all_courses_utils import (
    SINGLE_DEPT_COURSES,
    int_or_string,
    validate_semester,
)
from resources.departments import _depts_fetcher


def get_all_courses_mini(semester):
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
        soup = BeautifulSoup(resp.text, "html.parser")
        courses_list = soup.find("div", {"class": "courses-container"})
        for course in courses_list.find_all("div", {"class": "course"}):
            # basic info
            course_code = course.find("div", {"class": "course-id"}).text.strip()
            course_name = course.find("span", {"class": "course-title"}).text.strip()
            dept_courses.append(
                {
                    "course_code": course_code,
                    "course_name": course_name,
                }
            )
        all_courses.extend(dept_courses)
    return all_courses


class AllCoursesListMini(Resource):
    def get(self):
        parser = reqparse.RequestParser()
        parser.add_argument(
            "semester",
            type=int_or_string,
            required=True,
            location="args",
            help="Semester code is required, use the courses/semesters endpoint to get available semesters",
        )

        args = parser.parse_args()
        semester = validate_semester(args["semester"])

        all_courses = get_all_courses_mini(semester)
        if not all_courses:
            return {"message": "No courses found for the given parameters."}, 404
        return {"courses": all_courses}, 200
