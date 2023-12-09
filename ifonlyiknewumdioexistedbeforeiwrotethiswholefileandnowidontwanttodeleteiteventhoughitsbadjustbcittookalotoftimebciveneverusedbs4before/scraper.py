from datetime import datetime
import json
import re
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import requests


# terms = []
# for e in response.html.find('#term-id-input option'):
#     terms.append(e.attrs['value'])

header = {
    "Accept-Language": "es-ES,es;q=0.9",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
}

# dump all possible classes, only pull them once searched?


def dump():
    term = 202401
    json_object = json.dumps(get_course('CMSC132', '202401'), indent=4)

    # Writing to sample.json
    with open("dump.json", "w") as outfile:
        outfile.write(json_object)


def get_departments(term):
    departments = []
    url = f"https://app.testudo.umd.edu/soc/{term}/"
    response = BeautifulSoup(requests.get(
        url=url, headers=header).content, "html.parser")
    for e in response.find_all('div', class_='course-prefix'):
        departments.append({
            "departmentID": e.find('span', 'prefix-abbrev').text, "fullName": e.find('span', 'prefix-name').text,
        })
    return departments


def get_courses(departmentID, term):
    # still need gened codes
    # still need core groups whatever that means
    # make sure all sections, even async and blended show up
    courses = []
    url = f"https://app.testudo.umd.edu/soc/{term}/{departmentID}"
    response = BeautifulSoup(requests.get(
        url=url, headers=header).content, "html.parser")

    course_code = ""
    course_title = ""
    credits = ""
    grading_method = ""
    course_info = ""
    sections = []
    for e in response.find_all('div', class_='course'):
        course_code = e.find('div', class_="course-id").text
        course_title = e.find('span', class_="course-title").text
        credits = e.find('span', class_="course-min-credits").text
        grading_method = e.find(
            'span', class_="grading-method").text.replace('\n', '').replace('\t', '')
        i = e.find('div', 'approved-course-text')
        if i is not None:
            course_info = i.text.replace('\n', '').replace('\t', '')

        sections.append(get_sections(course_code, term=term))

        courses.append({
            "courseID": course_code, "courseTitle": course_title, "credits": credits, "gradingMethod": grading_method, "courseInfo": course_info, "sections": sections,
        })
    return courses


def get_sections(course_code, term, restrictions):
    sections = []
    departmentID = course_code[:3]
    url = f"https://app.testudo.umd.edu/soc/{term}/{departmentID}/{course_code}"
    response = BeautifulSoup(requests.get(
        url=url, headers=header).content, "html.parser")
    credits = int(response.find('span', class_="course-min-credits").text)
    for s in response.find_all('div', class_='section'):
        open_seats = int(s.find('span', class_='open-seats-count').text)
        if open_seats <= restrictions["minSeats"]:
            continue
        instructors = []
        for instructor in s.find_all('span', class_='section-instructor'):
            instructors.append(instructor.text)
        if any(x in instructors for x in restrictions["prohibitedInstructors"]):
            continue
        total_seats = int(s.find('span', class_='total-seats-count').text)
        section_id = s.find(
            'span', class_='section-id').text.replace('\n', '').replace('\t', '')
        waitlist_count = int(s.find('span', class_='waitlist-count').text)
        # waitlist link?

        class_info = []
        for c in s.find('div', class_='class-days-container').findChildren(recursive=False):

            day = c.find('div', class_='section-day-time-group')
            if day is not None:
                day = day.text.replace('\n', '').replace('\t', '')
            else:
                day = ""
            building = c.find('div', class_='section-class-building-group')
            if building is not None:
                building = building.text.replace('\n', '').replace('\t', '')
            else:
                building = ""
            class_type = c.find('span', class_='class-type')
            if class_type is not None:
                class_type = class_type.text.replace(
                    '\n', '').replace('\t', '')
            else:
                class_type = ""
            class_info.append({
                "days": time_converter(day), "building": building, "classType": class_type,
            })

        sections.append({
            "courseCode": course_code,
            "instructors": instructors, "totalSeats": total_seats, "openSeats": open_seats, "sectionID": section_id, "waitlistCount": waitlist_count, "classInfo": class_info, "credits": credits,
        })

    return sections


def time_converter(day_info):
    res = {}
    days = get_days(day_info)
    temp = re.sub(' ', '', day_info)
    temp = re.sub('M', '', temp)
    temp = re.sub('Tu', '', temp)
    temp = re.sub('W', '', temp)
    temp = re.sub('Th', '', temp)
    temp = re.sub('F', '', temp)
    day_split = temp.split('-')
    start_time = convert24(day_split[0])
    end_time = convert24(day_split[1])
    if days[0] == 1:
        res.update({'M': {
            "startTime": start_time, "endTime": end_time,
        }})

    if days[1] == 1:
        res['Tu'] = {
            "startTime": start_time, "endTime": end_time,
        }
    if days[2] == 1:
        res['W'] = {
            "startTime": start_time, "endTime": end_time,
        }
    if days[3] == 1:
        res['Th'] = {
            "startTime": start_time, "endTime": end_time,
        }
    if days[4] == 1:
        res['F'] = {
            "startTime": start_time, "endTime": end_time,
        }
    return res


def convert24(time):
    # Parse the time string into a datetime object
    t = datetime.strptime(time, '%I:%M%p')
    # Format the datetime object into a 24-hour time string
    return t.strftime('%H:%M:%S')


def get_days(day_info):
    res = [0, 0, 0, 0, 0]
    if 'M' in day_info:
        res[0] = 1
    if 'Tu' in day_info:
        res[1] = 1
    if 'W' in day_info:
        res[2] = 1
    if 'Th' in day_info:
        res[3] = 1
    if 'F' in day_info:
        res[4] = 1
    return res


def get_course(course_code, term):
    departmentID = course_code[:3]
    url = f"https://app.testudo.umd.edu/soc/{term}/{departmentID}/{course_code}"
    response = BeautifulSoup(requests.get(
        url=url, headers=header).content, "html.parser")
    course_code = ""
    course_title = ""
    credits = ""
    grading_method = ""
    course_info = ""
    sections = []

    course_code = response.find('div', class_="course-id").text
    course_title = response.find('span', class_="course-title").text
    credits = response.find('span', class_="course-min-credits").text
    grading_method = response.find(
        'span', class_="grading-method").text.replace('\n', '').replace('\t', '')
    i = response.find('div', 'approved-course-text')
    if i is not None:
        course_info = i.text.replace('\n', '').replace('\t', '')

    sections.append(get_sections(course_code, term=term))
    return {
        "courseID": course_code, "courseTitle": course_title, "credits": credits, "gradingMethod": grading_method, "courseInfo": course_info, "sections": sections,
    }
