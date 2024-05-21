from datetime import datetime
from flask import json
import requests
from datetime import datetime



# backtracking function to create all possible schedules
def backtracking(assignment, variables, res, domains, found):
    # Base case: If the assignment is complete, add it to the result
    if len(assignment) == len(variables):
        string_rep = ""
        for key in assignment:
            string_rep += key + " " + assignment[key]['section_id']
        if string_rep not in found:
            res.append(assignment.copy())  # Make a deep copy of the assignment
            found.append(string_rep)
        else:
            print("Duplicate schedule found")
        return

    # Choose an unassigned variable
    var = get_unused_var(assignment, variables, domains)

    # Consider all possible values for the chosen variable
    for value in domains_values(var, assignment, domains):
        if is_valid(value, assignment):
            assignment[var] = value
            # Recursively call backtracking to continue building the assignment
            backtracking(assignment, variables, res, domains, found)
            # Backtrack: remove the current variable assignment
            del assignment[var]


def get_unused_var(assignment, variables, domains):
    unassigned_vars = [var for var in variables if var not in assignment]
    res = min(unassigned_vars, key=lambda var: len(domains[var]))
    return res


def domains_values(var, assignment, domains):
    return [domain for domain in domains[var] if domain not in assignment.values()]


def parse_time(time_str):
    # Helper function to convert time string to minutes since midnight
    parts = time_str[:-2].split(':')
    return int(parts[0]) * 60 + int(parts[1])


def check_overlap(course1, course2):

    # print(course1)
    for meeting1 in course1["meetings"]:
        for meeting2 in course2["meetings"]:
            # Check if the days are the same
            if any(day in meeting2["days"] for day in meeting1["days"]):
                # Check if there is a time overlap
                start_time1 = parse_time(meeting1["start_time"])
                end_time1 = parse_time(meeting1["end_time"])

                start_time2 = parse_time(meeting2["start_time"])
                end_time2 = parse_time(meeting2["end_time"])

                # Check for overlap
                if (start_time1 < end_time2) and (start_time2 < end_time1):
                    return True  # Time overlap found

    return False  # No time overlap


def is_valid(value, assignment):
    # Check for overlap
    for assigned_value in assignment.values():
        if check_overlap(value, assigned_value):
            return False

    # TODO: check for credit limits / minimums

    return True



def parse_time(time_str):
    return datetime.strptime(time_str, '%H:%M%p').time()
def clean_sections(sections, restrictions):
    res = []
    for section in sections:
        clean = True
        for instructor in section['instructors']:
            if instructor in restrictions['prohibitedInstructors']:
                clean = False
        if clean:
            for meeting in section['meetings']:
                if restrictions['prohibitedTimes']:
                    for time in restrictions['prohibitedTimes']:
                        if time["day"] in meeting['days']:
                            start_time = parse_time(time['start'])
                            end_time = parse_time(time['end'])
                            start_time2 = parse_time(meeting["start_time"])
                            end_time2 = parse_time(meeting["end_time"])
                            if (start_time < end_time2) and (start_time2 < end_time):
                                clean = False  # Time overlap found
                                break
                    if not clean:
                        break
        if clean:
            res.append(section)
        else:
            print("Prohibited time or instructor for section " +
                  section['section_id'])
    return res


def create_schedule(wanted_classes, restrictions):
    # Initialize your variables, res, and seen here
    variables = wanted_classes
    res = []

    domains = {}
    no_open_sections = []

    # TODO: implement required classes and restrictions more effectively
    # required_classes = restrictions.get('required_classes', [])

    # Call your backtracking function with the input data
    for course in variables:
        parameters = {
            "course_id": course,
            # TODO: need to make this based on restrictions
            "semester": "202408"
        }

        sections = clean_sections(requests.get(
            "https://api.umd.io/v1/courses/sections", params=parameters).json(), restrictions)
        if len(sections) == 0:
            print("No possible sections for " + course)
            no_open_sections.append(course)
        else:
            for section in sections:
                if int(section["open_seats"]) < restrictions['minSeats']:
                    print("Not enough open seats for section " +
                          section['section_id'])
                else:
                    if course not in domains:
                        domains[course] = []
                    domains[course].append(section)
    print(domains.keys())
    if len(no_open_sections) == len(variables):
        print("No open sections for any classes.")
    elif no_open_sections:
        print("Classes with no open sections: " + ', '.join(no_open_sections))
    found = []
    backtracking({}, variables, res, domains, found)

    # Return the result
    print(res)
    return res
