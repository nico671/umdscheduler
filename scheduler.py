from collections import OrderedDict
from scraper import *
import json

res = []
seen = set()


def backtracking(assignment, variables, res, seen, domains, required_classes):
    if len(variables) == len(assignment):
        seen_string = ""
        for c in assignment.values():
            seen_string += c['courseCode'] + c['sectionID']
        if seen_string not in seen:
            # Check if all required classes are in the assignment
            if all(req_class in assignment for req_class in required_classes):
                res.append(assignment.copy())
        return
    
    var = get_unused_var(assignment, variables, domains)
    for value in domains_values(var, assignment, domains):
        validity = is_valid(value, assignment)
        if validity:
            assignment[var] = value
            backtracking(assignment, variables, res, seen, domains, required_classes)
        assignment.pop(var, None)

def get_unused_var(assignment, variables, domains):
    unassigned_vars = [var for var in variables if var not in assignment]
    res = min(unassigned_vars, key=lambda var: len(domains[var]))
    return res

def domains_values(var, assignment, domains):
    return [domain for domain in domains[var] if domain not in assignment.values()]

def check_overlap(sect1, sect2):
    for times in sect1["classInfo"]:
        for other_times in sect2["classInfo"]:
            for k in times['days'].keys():
                if k in other_times['days']:
                    has_overlap = check_overlap_helper(times['days'][k], other_times['days'][k])
                    if has_overlap:
                        return True
    return False

def check_overlap_helper(first_inter, second_inter):
    if (first_inter['startTime'] < second_inter['startTime'] < first_inter['endTime']) or (first_inter['startTime'] < second_inter['endTime'] < first_inter['endTime']) or (second_inter['startTime'] <= first_inter['startTime'] and second_inter['endTime'] >= first_inter['endTime']):
        return True
    elif (second_inter['startTime'] < first_inter['startTime'] < second_inter['endTime']) or (second_inter['startTime'] < first_inter['endTime'] < second_inter['endTime']) or (first_inter['startTime'] <= second_inter['startTime'] and first_inter['endTime'] >= second_inter['endTime']):
        return True
    return False

def is_valid(value, assignment):
    # Check for overlap
    for assigned_value in assignment.values():
        if check_overlap(value, assigned_value):
            return False

    # Check for credit limit
    total_credits = sum([course['credits'] for course in assignment.values()]) + value['credits']
    if total_credits > 20:
        return False

    return True

def create_schedule(wanted_classes, restrictions):
    # Initialize your variables, res, and seen here
    variables = wanted_classes
    res = []
    seen = set()
    domains = {}
    no_open_sections = []
    required_classes = restrictions.get('required_classes', [])

    # Call your backtracking function with the input data
    for course in variables:
        sections = get_sections(course, "202401", restrictions)
        if len(sections) == 0:
            print("No possible sections for " + course)
            no_open_sections.append(course)
        else:
            domains[course] = sections

    if len(no_open_sections) == len(variables):
        print("No open sections for any classes.")
    elif no_open_sections:
        print("Classes with no open sections: " + ', '.join(no_open_sections))
    backtracking({}, variables, res, seen, domains, required_classes)

    # Return the result
    return res

# Test case
variables = ["ENGL142", "TLPL443", "WEID139T"]
restrictions = {"minSeats": 0, "prohibitedInstructors": [""], "prohibitedTimes": {}, "required_classes": ["ENGL142", "TLPL443", "WEID139T"]}
popper = create_schedule(variables, restrictions)
print(len(popper))
if len(popper) <= 0:
    print("No valid schedules created.")
else:
    json_object = json.dumps(popper, indent=4)
    with open("test.json", "w") as outfile:
        outfile.write(json_object)
