# ruff: noqa: E402, I001

import sys
import types
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from pydantic import ValidationError


fake_database = types.ModuleType("api.database")
setattr(fake_database, "get_db_connection", None)
sys.modules.setdefault("api.database", fake_database)

from api import main, scheduler  # noqa: E402
from api.schemas import ScheduleRequest  # noqa: E402


def section(section_code):
    return {
        "section_code": section_code,
        "instructors": [],
        "total_seats": 30,
        "open_seats": 30,
        "waitlist": 0,
        "meetings": [],
    }


class SchedulerBoundsTests(unittest.TestCase):
    def test_credit_and_schedule_limits(self):
        self.assertEqual(ScheduleRequest(max_credits=22).max_credits, 22)
        self.assertEqual(ScheduleRequest().max_credits, 22)

        with self.assertRaises(ValidationError):
            ScheduleRequest(max_credits=23)
        with self.assertRaises(ValidationError):
            ScheduleRequest(min_credits=23)
        with self.assertRaises(ValidationError):
            ScheduleRequest(max_schedules=51)

    def test_unique_combined_course_limit_and_duplicates(self):
        payload = ScheduleRequest(
            required_courses=["cmsc131", "CMSC131", "MATH140", "STAT100"],
            optional_courses=["STAT100", "ENGL101", "PHYS161"],
        )
        normalized_required = main._normalize_course_codes(payload.required_courses)
        normalized_optional = main._normalize_course_codes(payload.optional_courses)
        combined = set(normalized_required) | set(normalized_optional)
        self.assertEqual(len(combined), 5)

        with self.assertRaises(ValidationError):
            ScheduleRequest(max_credits=23)

    def test_api_accepts_ten_and_rejects_eleven_unique_courses(self):
        @contextmanager
        def fake_connection():
            yield object()

        ten_courses = [f"TEST{number}" for number in range(10)]
        accepted_payload = ScheduleRequest(
            required_courses=ten_courses[:5] + [ten_courses[0]],
            optional_courses=ten_courses[5:] + [ten_courses[5]],
        )
        with patch.object(main, "get_db_connection", fake_connection), patch.object(
            main, "_resolve_semester", return_value="202601"
        ), patch.object(
            main,
            "_get_course_min_credits_map",
            return_value={course: 1 for course in ten_courses},
        ), patch.object(
            main,
            "build_schedules",
            return_value={"schedules": [], "truncated": False},
        ) as build:
            response = main.generate_schedules(accepted_payload)

        self.assertEqual(response["schedules"], [])
        build.assert_called_once()

        eleven_courses = ten_courses + ["TEST10"]
        with self.assertRaises(main.HTTPException) as raised:
            main.generate_schedules(
                ScheduleRequest(
                    required_courses=eleven_courses,
                )
            )
        self.assertEqual(raised.exception.status_code, 422)

    def _build_with_domains(self, required, optional=None, *, budget_patches=None):
        domains = {
            course: [section(f"{course}-{number}") for number in range(3)]
            for course in set(required) | set(optional or [])
        }

        def preprocess(required_courses, **_kwargs):
            return required_courses, {
                course: domains[course] for course in required_courses
            }

        credits = {course: 3 for course in domains}
        patches = [
            patch.object(scheduler, "preprocess_restrictions", side_effect=preprocess),
            patch.object(
                scheduler,
                "_get_course_min_credits_map",
                return_value=credits,
            ),
            patch.object(scheduler, "get_prof_ratings", return_value={}),
        ]
        patches.extend(budget_patches or [])
        for active_patch in patches:
            active_patch.start()
        self.addCleanup(lambda: [active_patch.stop() for active_patch in reversed(patches)])
        return scheduler.build_schedules(
            required_courses=required,
            semester="202601",
            optional_courses=optional,
            max_credits=22,
        )

    def test_candidate_limit_bounds_ranked_records(self):
        result = self._build_with_domains(
            ["A"], budget_patches=[patch.object(scheduler, "MAX_CANDIDATE_SCHEDULES", 2)]
        )
        self.assertEqual(len(result["schedules"]), 2)
        self.assertTrue(result["truncated"])

    def test_node_limit_bounds_required_backtracking(self):
        result = self._build_with_domains(
            ["A"], budget_patches=[patch.object(scheduler, "MAX_SEARCH_NODES", 3)]
        )
        self.assertEqual(len(result["schedules"]), 2)
        self.assertTrue(result["truncated"])

    def test_optional_expansion_uses_the_required_search_budget(self):
        result = self._build_with_domains(
            ["A"],
            ["B"],
            budget_patches=[patch.object(scheduler, "MAX_SEARCH_NODES", 4)],
        )
        self.assertEqual(
            result["schedules"][0]["included_optional_courses"], []
        )
        self.assertTrue(result["truncated"])

    def test_complete_search_is_not_truncated(self):
        result = self._build_with_domains(["A"], budget_patches=[])
        self.assertEqual(len(result["schedules"]), 3)
        self.assertFalse(result["truncated"])

    def test_backtracking_generator_stops_at_node_limit(self):
        budget = scheduler.SearchBudget(node_limit=3)
        schedules = list(
            scheduler.backtrack_schedules(
                ["A"], {"A": [section("A-1"), section("A-2"), section("A-3")]}, budget=budget
            )
        )
        self.assertEqual(len(schedules), 2)
        self.assertEqual(budget.nodes_visited, 3)
        self.assertTrue(budget.truncated)

    def test_required_course_without_sections_returns_empty_complete_result(self):
        with patch.object(
            scheduler,
            "preprocess_restrictions",
            return_value=(['A'], {"A": []}),
        ), patch.object(
            scheduler,
            "_get_course_min_credits_map",
            return_value={"A": 3},
        ):
            result = scheduler.build_schedules(
                required_courses=["A"], semester="202601", max_credits=22
            )
        self.assertEqual(result, {"schedules": [], "truncated": False})


if __name__ == "__main__":
    unittest.main()
