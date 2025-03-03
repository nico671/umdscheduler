from statistics import mean

import requests

# backtracking function to create all possible schedules


def backtracking(assignment, variables, res, domains):
    # Base case: If the assignment is complete, add it to the result
    if len(assignment) == len(variables):
        prof_weights = []
        for cla in assignment:
            sect = assignment[cla]
            prof_weights.append(sect["prof_weight"])

        assignment["prof_weight"] = round(mean(prof_weights), 2)

        # print(assignment['prof_weight'])
        res.append(assignment.copy())  # Make a deep copy of the assignment
        assignment.pop("prof_weight")
        return

    # Choose an unassigned variable
    var = get_unused_var(assignment, variables, domains)

    # Consider all possible values for the chosen variable
    for value in domains_values(var, assignment, domains):
        if is_valid(value, assignment):
            assignment[var] = value
            # Recursively call backtracking to continue building the assignment
            backtracking(assignment, variables, res, domains)
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
    parts = time_str[:-2].split(":")
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
                    return True

    return False  # No time overlap


def is_valid(value, assignment):
    # Check for overlap

    for assigned_value in assignment.values():
        if (
            check_overlap(value, assigned_value)
            and value["section_id"] != assigned_value["section_id"]
        ):
            # print("there is an overlap")
            return False

    # TODO: check for credit limits / minimums
    return True


def clean_sections(sections, restrictions):
    res = []
    for section in sections:
        # if int(section["open_seats"]) < 1:
        #     print("No open seats for section " + section["section_id"])
        #     clean = False
        clean = True
        for instructor in section["instructors"]:
            if instructor.lower() in [
                x.lower() for x in restrictions["prohibitedInstructors"]
            ]:
                print("Prohibited instructor for section " + section["section_id"])
                clean = False
        if clean:
            for meeting in section["meetings"]:
                if restrictions["prohibitedTimes"]:
                    for time in restrictions["prohibitedTimes"]:
                        # print(time)
                        if time["days"] in meeting["days"]:
                            start_time = parse_time(time["start_time"])
                            end_time = parse_time(time["end_time"])
                            start_time2 = parse_time(meeting["start_time"])
                            end_time2 = parse_time(meeting["end_time"])
                            if (start_time < end_time2) and (start_time2 < end_time):
                                print(
                                    "Prohibited time for section "
                                    + section["section_id"]
                                )
                                clean = False

        if clean:
            res.append(section)
    return res


def weight_schedules(domains):
    professor_weights = {}
    for domain in domains:
        sections = domains[domain]
        for section in sections:
            section["prof_weight"] = 0
            # print(section)
            for instructor in section["instructors"]:
                if instructor not in professor_weights:
                    res = requests.get(
                        "https://planetterp.com/api/v1/professor",
                        params={"name": instructor},
                    ).json()
                    # print(res)
                    if "error" not in res and res["average_rating"] is not None:
                        professor_weights[instructor] = round(res["average_rating"], 2)
                    else:
                        professor_weights[instructor] = 0
                if section["prof_weight"] != 0:
                    section["prof_weight"] = mean(
                        [section["prof_weight"], professor_weights[instructor]]
                    )
                section["prof_weight"] = professor_weights[instructor]
            # weight by professor ranking (higher is better)
            # sourced from planetterp
    return domains


def create_schedule(wanted_classes, restrictions):
    # Initialize your variables, res, and seen here
    variables = wanted_classes
    res = []

    domains = {}
    no_open_sections = []

    # TODO: implement required classes and restrictions more effectively
    # required_classes = restrictions.get('required_classes', [])

    # Call your backtracking function with the input data
    print("Wanted classes:", variables)
    for course in variables:
        parameters = {
            "course_id": course,
            # TODO: need to make this based on restrictions
            "semester": "202508",
        }

        try:
            response = requests.get(
                "https://api.umd.io/v1/courses/sections", params=parameters
            )
            response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xx
        except requests.RequestException as e:
            return {
                "error": f"An error occurred when trying to get sections for {course}: {str(e)}"
            }
        sections = clean_sections(
            requests.get(
                "https://api.umd.io/v1/courses/sections", params=parameters
            ).json(),
            restrictions,
        )
        if len(sections) == 0:
            print("No possible sections for " + course)
            no_open_sections.append(course)
        else:
            for section in sections:
                if course not in domains:
                    domains[course] = []
                domains[course].append(section)
    print("Populated domains:", domains, "\n")
    if len(no_open_sections) == len(variables):
        return {"error": "No possible sections for any of the requested courses"}
    if len(no_open_sections) > 0:
        return {
            "error": "No open sections for any of the following requested courses",
            "courses": no_open_sections,
        }
    for course in variables:
        if course not in domains:
            return {"error": "No possible sections for " + course}
    weight_schedules(domains)
    backtracking({}, variables, res, domains)
    # print(res)
    if len(res) == 0:
        print("No possible schedules found")
        return {"error": "No possible schedules found"}
    # print("sorted", sorted(res, key=lambda d: d["prof_weight"]))
    return sorted(res, key=lambda d: d["prof_weight"])
