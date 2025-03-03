# UMD Schedule Generator Backend

A Python-based backend service for generating class schedules for University of Maryland students.

## Features

- Automatic schedule generation based on desired courses
- Conflict detection and resolution
- Professor rating integration via PlanetTerp
- Support for custom restrictions:
  - Prohibited instructors
  - Time constraints
  - Section preferences

## Prerequisites

- Python 3.13+
- Flask
- Requests library

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd umdscheduler_backend
```

2. Install dependencies:

```bash
pip install flask flask-cors requests
```

3. Run the server:

```bash
python api.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### POST /schedule

Creates possible schedules based on provided courses and restrictions.

**Request Body:**

```json
{
  "wanted_classes": ["CMSC330", "CMSC351"],
  "restrictions": {
    "prohibitedInstructors": ["Smith, John"],
    "prohibitedTimes": [
      {
        "day": "M",
        "start": "10:00am",
        "end": "11:00am"
      }
    ]
  }
}
```

**Response:**
Returns an array of possible schedules sorted by professor ratings.

## Contributing

Feel free to open issues and submit pull requests.

## License

MIT
