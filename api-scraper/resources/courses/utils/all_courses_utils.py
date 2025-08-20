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


def validate_min_credits(min_credits_input):
    """
    Validate and parse min_credits parameter.
    Accepts either:
    - A number (int/float) with default 'geq' comparator
    - A string in format "<number>|<comparator>"

    Returns tuple: (credits_value, comparator)
    """
    valid_comparators = ["eq", "lt", "gt", "geq", "leq"]

    # If input is a number, use default 'leq' comparator
    if isinstance(min_credits_input, (int, float)):
        return int(min_credits_input), "leq"

    # If input is a string, parse it
    if isinstance(min_credits_input, str):
        # Check if it contains the separator
        if "|" in min_credits_input:
            parts = min_credits_input.split("|")
            if len(parts) != 2:
                raise ValueError(
                    "min_credits must be in format '<number>|<comparator>' or just a number"
                )

            credits_str, comparator = parts

            # Validate comparator
            if comparator not in valid_comparators:
                raise ValueError(
                    f"Invalid comparator '{comparator}'. Must be one of: {valid_comparators}"
                )

            # Validate and convert credits
            try:
                credits = int(credits_str)
                if credits < 0:
                    raise ValueError("Credits must be non-negative")
                return credits, comparator
            except ValueError:
                raise ValueError("Credits must be a valid integer")
        else:
            # String without separator, treat as number with default comparator
            try:
                credits = int(min_credits_input)
                if credits < 0:
                    raise ValueError("Credits must be non-negative")
                return credits, "geq"
            except ValueError:
                raise ValueError(
                    "min_credits must be a valid integer or in format '<number>|<comparator>'"
                )

    raise ValueError(
        "min_credits must be a number or string in format '<number>|<comparator>'"
    )


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


def validate_seats(seats_input, field_name="seats"):
    """
    Validate and parse seats parameter (total_seats, open_seats, waitlist_count).
    Accepts either:
    - A number (int/float) with default 'geq' comparator
    - A string in format "<number>|<comparator>"

    Returns tuple: (seats_value, comparator)
    """
    valid_comparators = ["eq", "lt", "gt", "geq", "leq"]

    # If input is a number, use default 'leq' comparator
    if isinstance(seats_input, (int, float)):
        return int(seats_input), "leq"

    # If input is a string, parse it
    if isinstance(seats_input, str):
        # Check if it contains the separator
        if "|" in seats_input:
            parts = seats_input.split("|")
            if len(parts) != 2:
                raise ValueError(
                    f"{field_name} must be in format '<number>|<comparator>' or just a number"
                )

            seats_str, comparator = parts

            # Validate comparator
            if comparator not in valid_comparators:
                raise ValueError(
                    f"Invalid comparator '{comparator}'. Must be one of: {valid_comparators}"
                )

            # Validate and convert seats
            try:
                seats = int(seats_str)
                if seats < 0:
                    raise ValueError(f"{field_name} must be non-negative")
                return seats, comparator
            except ValueError:
                raise ValueError(f"{field_name} must be a valid integer")
        else:
            # String without separator, treat as number with default comparator
            try:
                seats = int(seats_input)
                if seats < 0:
                    raise ValueError(f"{field_name} must be non-negative")
                return seats, "geq"
            except ValueError:
                raise ValueError(
                    f"{field_name} must be a valid integer or in format '<number>|<comparator>'"
                )

    raise ValueError(
        f"{field_name} must be a number or string in format '<number>|<comparator>'"
    )


def validate_section_ids(section_ids_str):
    """
    Validate and parse section IDs parameter.
    Accepts comma-separated section IDs in format DEPTNNN-XXXX.
    
    Returns list of validated section IDs.
    """
    if not section_ids_str:
        raise ValueError("section_ids parameter is required")
    
    section_ids = [sid.strip().upper() for sid in section_ids_str.split(",")]
    
    for section_id in section_ids:
        # Validate format: should be like CMSC131-0101, ENGL101-0201, etc.
        if "-" not in section_id:
            raise ValueError(f"Invalid section ID format: '{section_id}'. Expected format: DEPTNNN-XXXX")
        
        course_part, section_part = section_id.split("-", 1)
        
        # Validate course part (should be department code + course number)
        if len(course_part) < 4:
            raise ValueError(f"Invalid course part in section ID: '{section_id}'. Course part too short.")
        
        # Validate section part (should be 4 digits typically, but allow flexibility)
        if len(section_part) < 1:
            raise ValueError(f"Invalid section part in section ID: '{section_id}'. Section part missing.")
    
    return section_ids
