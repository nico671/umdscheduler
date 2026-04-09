# UMDScheduler

UMDScheduler is a course planning and schedule generation tool for the University of Maryland. It combines a FastAPI backend with a Svelte 5 frontend to help students browse course offerings, inspect section details, apply scheduling constraints, and generate conflict-free schedules.

## What it does

UMDScheduler is designed to make schedule planning less painful and a lot more visual. The app lets you:

- Search the full course catalog by course code, title, level, or GEN ED code.
- Build a list of required courses and optional courses.
- Inspect course details, sections, instructors, seat availability, and meeting times.
- Exclude specific professors from generated schedules.
- Block off specific days and time slots.
- Filter generated schedules by minimum/maximum credit load.
- Prefer schedules that only use open-seat sections.
- View generated schedules in a weekly calendar layout.
- Compare schedules using instructor ratings and section GPA data from PlanetTerp.

## Features

### Course discovery

- Loads the course catalog from the backend and caches it locally for faster repeat visits.
- Supports free-text search across course ID, title, level, and GEN ED codes.
- Prevents duplicate selection of the same course as required and optional.

### Course details

- Opens a modal with course metadata and all available sections.
- Shows section codes, instructors, seat counts, waitlist counts, and meeting patterns.
- Fetches extra course information such as average GPA and professor ratings when available.

### Schedule building

- Lets you choose required and optional courses before generating schedules.
- Supports professor exclusions and blocked time windows.
- Can restrict results to sections with open seats only.
- Enforces minimum and maximum credit bounds.
- Ranks schedules by professor rating and credit total.

### Calendar view

- Renders each generated schedule in a weekly timetable.
- Lays out overlapping meetings in separate lanes so conflicts are visible.
- Uses color-coded course blocks for easier scanning.
- Lets you open a schedule entry to inspect section details.

### Persistence and caching

- Stores catalog and external API responses in memory and localStorage.
- Reduces repeat requests to the backend and PlanetTerp.

## Technical details

### Frontend

- Built with **Svelte 5** and **Vite**.
- Uses Svelte runes such as `$state` and `$derived` for local state and computed values.
- Component structure lives under `frontend/src/lib/components`.
- Shared client logic lives under `frontend/src/lib/utils`.
- Runtime env values are validated in `frontend/src/lib/config/runtimeConfig.js`.
- The frontend reads its backend API base URL from `frontend/.env` via `VITE_API_BASE_URL`.
- The UI is split into reusable pieces for course lists, schedule calendar, and modals.

### Backend environment

- Built with **FastAPI**.
- Uses **psycopg2** and a threaded connection pool for database access.
- Centralizes runtime config in `backend/common/settings.py` and validates env values on startup.
- Adds CORS middleware so the frontend can call the API during development and deployment.

## Environment setup

### Backend

1. Copy `backend/.env.example` to `backend/.env`.
2. Set required values:
   - `CORS_ORIGINS`
   - `CORS_ALLOW_CREDENTIALS`
   - `DATABASE_URL` (optional for local DB fallback)
   - `DB_POOL_MIN`, `DB_POOL_MAX`
   - `DB_CONNECT_TIMEOUT`, `DB_KEEPALIVES*`
3. Optional profile variable: `APP_ENV=development|staging|production|test`.

### Frontend environment

1. Copy `frontend/.env.example` to `frontend/.env`.
2. Set `VITE_API_BASE_URL` to the backend origin (for example, `http://localhost:8000`).

### Validation behavior

- Invalid backend env values fail fast during startup with a clear configuration error.
- Invalid frontend `VITE_API_BASE_URL` fails fast in the client runtime config module.

### Data model and API

The backend exposes endpoints for:

- `GET /api/v1/status` — latest section update timestamp.
- `GET /api/v1/semesters` — available semesters.
- `GET /api/v1/departments` — department codes and names.
- `GET /api/v1/courses` — searchable course summaries.
- `GET /api/v1/courses/{course_code}` — full course detail with sections and meetings.
- `GET /api/v1/sections` — section search by instructor, meeting days, and status.
- `POST /api/v1/schedules` — schedule generation based on constraints.

### Schedule generation logic

- Required courses are expanded into section domains from the database.
- Time conflicts are checked by comparing overlapping meeting days and times.
- Optional courses are added on top of valid required-course combinations when credit limits allow it.
- Section-level GPA data is calculated using PlanetTerp grade distributions.
- Schedule ratings are averaged across instructors to help compare outcomes.

### External services

- **PlanetTerp** APIs are used for professor ratings, course GPA data, and grade distributions.
- **PostgreSQL** stores course, section, meeting, semester, and department data.

## Project structure

- `backend/api` — FastAPI application, schedule engine, schemas, and database helpers.
- `backend/common` — shared database configuration.
- `backend/scraper` — scripts for ingesting and updating course data.
- `frontend/src/lib/components` — UI components for lists, modals, controls, and the calendar.
- `frontend/src/lib/utils` — data fetching, caching, and schedule formatting helpers.

## Screenshots

Add screenshots here later:

| Screenshot | Description |
| --- | --- |
| `./screenshots/home.png` | Main dashboard / course search view |
| `./screenshots/course-detail.png` | Course detail modal |
| `./screenshots/restrictions.png` | Scheduling restrictions panel |
| `./screenshots/calendar.png` | Generated schedule calendar |

## Notes

- The backend allows only the deployed Vercel origin by default and can be overridden with `CORS_ORIGINS` if needed.
- Cached data is stored in memory first and then mirrored to localStorage when possible.

## License

No license has been specified yet.
