from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# Define the Meeting structure
class Meeting(BaseModel):
    days: Optional[str]
    start_time: Optional[str]
    end_time: Optional[str]
    building_code: Optional[str]
    room: Optional[str]
    class_type: Optional[str]


# Define the Section structure
class Section(BaseModel):
    section_code: str
    instructors: List[str]
    total_seats: int
    open_seats: int
    waitlist: int
    meetings: List[Meeting] = Field(default_factory=list)


# Define the top-level Course structure
class CourseDetail(BaseModel):
    course_code: str
    title: Optional[str]
    credits: Optional[str]
    description: Optional[str]
    attributes: Optional[Dict[str, Any]]
    sections: List[Section] = Field(default_factory=list)


class StatusResponse(BaseModel):
    last_updated: Optional[datetime]


class Semester(BaseModel):
    semester_code: str
    name: str
    is_active: bool


class Department(BaseModel):
    department_code: str
    name: str


class CourseSummary(BaseModel):
    course_code: str
    department_code: Optional[str]
    title: Optional[str]
    credits: Optional[str]
    description: Optional[str]
    grading_options: List[str] = Field(default_factory=list)
    gened_codes: List[str] = Field(default_factory=list)
    attributes: Optional[Dict[str, Any]]


class SectionSearchResult(BaseModel):
    course_code: str
    course_title: Optional[str]
    semester_code: str
    section_code: str
    instructors: List[str] = Field(default_factory=list)
    total_seats: int
    open_seats: int
    waitlist: int
    meetings: List[Meeting] = Field(default_factory=list)


class TimeConstraint(BaseModel):
    day: str
    start_time: str
    end_time: str


class ScheduleRequest(BaseModel):
    required_courses: List[str] = Field(default_factory=list)
    semester: Optional[str] = None
    excluded_profs: List[str] = Field(default_factory=list)
    time_constraints: List[TimeConstraint] = Field(default_factory=list)
    max_schedules: int = Field(default=50, ge=1, le=500)


class ScheduledSection(Section):
    course_code: str
    avg_prof_gpa_in_class: Optional[float] = None


class ScheduleResult(BaseModel):
    sections: List[ScheduledSection] = Field(default_factory=list)
    average_professor_rating: Optional[float] = None
