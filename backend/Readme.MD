# UMDScheduler

UMDScheduler is a Python-based application that helps University of Maryland students to create their class schedules. It takes into account various factors such as preferred classes, prohibited instructors, and unavailable times to generate a schedule that fits the student's needs.

## Features

- **Schedule Creation**: Input your desired classes and let the application generate a schedule for you.
- **Instructor Restrictions**: Specify instructors you want to avoid.
- **Time Restrictions**: Specify times during which you are unavailable.

## Code Overview

The main logic of the application is contained in two Python files:

- `api.py`: This file contains the Flask API endpoints that the frontend interacts with. It receives the user's input, calls the scheduling function with this input, and returns the result.

- `scheduler.py`: This file contains the scheduling logic. The `create_schedule` function takes a list of desired classes and a dictionary of restrictions, and returns a schedule that fits these requirements. The `clean_sections` function is used to filter out sections that don't meet the restrictions.
