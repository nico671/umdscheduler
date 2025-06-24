from resources.courses.semesters import _semester_fetcher

SINGLE_DEPT_COURSES = "https://app.testudo.umd.edu/soc/{semester}/{dept_code}"


def int_or_string(val):
    try:
        return int(val)
    except (ValueError, TypeError):
        return val


def validate_semester(semester):
    semesters = _semester_fetcher()
    # print(f"Available semesters: {semesters}")
    if not any(int(s["code"]) == int(semester) for s in semesters):
        raise ValueError(
            f"Invalid semester code: {semester}. Use the courses/semesters endpoint to get available semesters."
        )
    return semester


def validate_min_credits(min_credits):
    parts = min_credits.split("|", 1)
    min_credits = parts[0]
    min_credits_comparator = parts[1] if len(parts) == 2 else None
    # print(f"Parsed min_credits: {min_credits}, comparator: {min_credits_comparator}")
    if not min_credits.isdigit():
        raise ValueError(f"Invalid credits value: {min_credits}. Must be a number.")
    min_credits = int(min_credits)
    if min_credits < 0 or min_credits > 10:
        raise ValueError(
            f"Invalid credits value: {min_credits}. Must be between 0 and 10."
        )
    if min_credits_comparator not in [None, "eq", "lt", "gt", "geq", "leq"]:
        raise ValueError(
            f"Invalid credits comparator: {min_credits_comparator}. Must be one of 'eq', 'lt', 'gt', 'geq', 'leq'."
        )
    return min_credits, min_credits_comparator


def validate_geneds(gened_str):
    if not gened_str:
        return None
    gened_list = [gen.strip().upper() for gen in gened_str.split(",")]
    valid_geneds = [
        "FSAW",
        "FSAR",
        "FSMA",
        "FSOC",
        "FSPW",
        "DSHS",
        "DSSP",
        "DSNS",
        "DSHU",
        "DSNL",
        "DVCC",
        "DVUP",
        "SCIS",
    ]
    for gened in gened_list:
        if gened not in valid_geneds:
            raise ValueError(f"Invalid general education code: {gened}.")
    return gened_list
