from collections import OrderedDict
from datetime import datetime
import os
from scraper import *
import json

res = []
seen = set()
def backtracking(assignment):
    if len(assignment) == len(variables):
        seen_string = ""
        for c in assignment.values():
            seen_string += c['courseCode'] + c['sectionID']
        if seen_string not in seen:
            res.append(assignment.copy())
        return
    
    var = get_unused_var(assignment)
    for value in domains_values(var): 
        validity = is_valid(value, assignment)
        if validity == True:
            assignment[var] = value 
            backtracking(assignment) 
        assignment.pop(var, None)

def get_unused_var(assignment):
    unassigned_vars = [var for var in variables if var not in assignment] 
    res = min(unassigned_vars, key=lambda var: len(domains[var]))
    return res

def domains_values(var):
    return domains[var]

def check_overlap(sect1, sect2):
    for times in sect1["classInfo"]:
        for other_times in sect2["classInfo"]:
            for k in times['days'].keys():
                if k in other_times['days']:
                    has_overlap = check_overlap_helper(times['days'][k], other_times['days'][k])
                    if has_overlap:
                        return True
    else:
        return False

def check_overlap_helper(first_inter,second_inter):
    if (first_inter['startTime'] < second_inter['startTime'] < first_inter['endTime']) or (first_inter['startTime'] < second_inter['endTime'] < first_inter['endTime']) or (second_inter['startTime'] <= first_inter['startTime'] and second_inter['endTime'] >= first_inter['endTime']): 
        return True
    elif (second_inter['startTime'] < first_inter['startTime'] < second_inter['endTime']) or (second_inter['startTime'] < first_inter['endTime'] < second_inter['endTime']) or (first_inter['startTime'] <= second_inter['startTime'] and first_inter['endTime'] >= second_inter['endTime']):
        return True
    return False

def is_valid(value, assignment): 
    if len(assignment) == 0:
        return True
    total_credits = 0
    for s in assignment.values():
        has_overlap = check_overlap(value,s)
        if has_overlap == True:
            return False
        total_credits += s['credits']
    # TODO: add dynamic credit limit
    if total_credits > 18:
        return False
    return True


variables = {"CMSC132" : True, "MATH141" : True, "ASTR101" : False, "ANTH222" : False, "ECON200" : False}

domains = {}

restrictions = {"minSeats" : 0, "prohibitedInstructors" : [""], "prohibitedTimes" : {}}


for course in variables:
    sections = get_sections(course, "202401", restrictions)
    if len(sections) == 0:
        print("No possible sections for " + course)
    domains[course] = sections

backtracking(OrderedDict())
json_object = json.dumps(res, indent=4)
with open("test.json", "w") as outfile:
    outfile.write(json_object)
