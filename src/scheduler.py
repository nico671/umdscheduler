from collections import OrderedDict
import json
from datetime import datetime

import requests

# backtracking function to create all possible schedules
def backtracking(assignment, variables, res, domains):
    # If the assignment is complete and valid, add it to the result
    if len(assignment) == len(variables):
        res.append(assignment.copy())
        return

    # Select an unassigned variable
    for var in variables:
        if var not in assignment:
            # Try all values in the domain of the variable
            for value in domains[var]:

                # If the assignment is valid, recurse on the remaining variables
                if is_valid(value, assignment):
                    assignment[var] = value
                    backtracking(assignment, variables, res,
                                 domains)
                # Remove the assignment
                del assignment[var]


def get_unused_var(assignment, variables, domains):
    unassigned_vars = [var for var in variables if var not in assignment]
    res = min(unassigned_vars, key=lambda var: len(domains[var]))
    return res

def domains_values(var, assignment, domains):
    return [domain for domain in domains[var] if domain not in assignment.values()]


def check_overlap(course1, course2):
    def parse_time(time_str):
        # Helper function to convert time string to minutes since midnight
        parts = time_str[:-2].split(':')
        return int(parts[0]) * 60 + int(parts[1])

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

# def clean_sections(response, restrictions):
#     sections = response.json()
#     res = []
#     for section in sections:
#         if section['instructors'][0] not in restrictions['prohibitedInstructors']:
#             if section['section_id'] not in restrictions['prohibitedTimes']:
#                 res.append(section)
#     return res


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
            "open_seats": "1|geq",
            "semester": "202401"
        }

        sections = requests.get(
            "https://api.umd.io/v1/courses/sections", params=parameters).json()
        if len(sections) == 0:
            print("No possible sections for " + course)
            no_open_sections.append(course)
        else:
            domains[course] = sections

    if len(no_open_sections) == len(variables):
        print("No open sections for any classes.")
    elif no_open_sections:
        print("Classes with no open sections: " + ', '.join(no_open_sections))
    backtracking({}, variables, res, domains)

    # Return the result
    return res
