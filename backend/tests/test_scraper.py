import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import requests

from scraper import scraper


class FakeResponse:
    def __init__(self, text="", status_code=200):
        self.text = text
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, response):
        self.response = response

    def get(self, _url, timeout):
        self.timeout = timeout
        return self.response


class ScraperTests(unittest.TestCase):
    def test_scraper_module_imports_without_database_connection(self):
        backend_dir = Path(__file__).resolve().parents[1]
        result = subprocess.run(
            [sys.executable, "-c", "import scraper.scraper"],
            cwd=backend_dir,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)

    def test_homepage_http_errors_fail_scrape(self):
        for status_code in (404, 429, 500):
            with self.subTest(status_code=status_code), patch.object(
                scraper.requests,
                "get",
                return_value=FakeResponse(status_code=status_code),
            ):
                with self.assertRaises(requests.HTTPError):
                    scraper.scrape_all_available_semesters()

    def test_department_and_course_http_errors_fail_scrape(self):
        with patch.object(
            scraper,
            "get_thread_session",
            return_value=FakeSession(FakeResponse(status_code=429)),
        ):
            with self.assertRaises(requests.HTTPError):
                scraper.scrape_available_course_codes_for_dept("CMSC", "Computer", "202601")

        with patch.object(
            scraper,
            "get_thread_session",
            return_value=FakeSession(FakeResponse(status_code=500)),
        ):
            with self.assertRaises(requests.HTTPError):
                scraper.scrape_course_info_for_course_code_with_sections(
                    "CMSC131", "202601"
                )

    def test_request_timeout_fails_scrape(self):
        with patch.object(
            scraper.requests, "get", side_effect=requests.Timeout("timed out")
        ):
            with self.assertRaises(requests.Timeout):
                scraper.scrape_all_available_semesters()

    def test_missing_required_homepage_html_fails_scrape(self):
        cases = (
            ("missing selector", "<html></html>", "semester selector"),
            (
                "missing current semester",
                '<select id="term-id-input"><option value="202601">Spring</option></select>',
                "current semester",
            ),
            (
                "missing department container",
                '<select id="term-id-input"><option selected value="202601">Spring</option></select>',
                "department container",
            ),
            (
                "empty department list",
                '<select id="term-id-input"><option selected value="202601">Spring</option></select>'
                '<div id="course-prefixes-page"></div>',
                "empty department list",
            ),
        )
        for name, html, message in cases:
            with self.subTest(name=name), patch.object(
                scraper.requests, "get", return_value=FakeResponse(html)
            ):
                with self.assertRaisesRegex(scraper.ScrapeError, message):
                    scraper.scrape_all_available_departments_for_current_semester()

    def test_empty_and_unparseable_course_codes_fail_scrape(self):
        for html, message in (
            ("<html></html>", "empty course-code list"),
            ('<div class="course" id="BAD"></div>', "Cannot parse course code"),
        ):
            with self.subTest(message=message), patch.object(
                scraper,
                "get_thread_session",
                return_value=FakeSession(FakeResponse(html)),
            ):
                with self.assertRaisesRegex(scraper.ScrapeError, message):
                    scraper.scrape_available_course_codes_for_dept(
                        "CMSC", "Computer", "202601"
                    )

    def test_one_department_worker_failure_fails_complete_collection(self):
        def scrape_department(dept_code, _dept_name, _semester):
            if dept_code == "FAIL":
                raise scraper.ScrapeError("broken department")
            return ["CMSC131"]

        with patch.object(
            scraper,
            "scrape_available_course_codes_for_dept",
            side_effect=scrape_department,
        ):
            with self.assertRaisesRegex(scraper.ScrapeError, "1 department worker"):
                scraper.scrape_available_course_codes_for_all_depts(
                    [("FAIL", "Broken"), ("CMSC", "Computer")], "202601"
                )

    def test_one_course_worker_failure_fails_complete_collection(self):
        def scrape_course(course_code, _semester):
            if course_code == "FAIL101":
                raise scraper.ScrapeError("broken course")
            return {"course_code": course_code, "sections": []}

        with patch.object(
            scraper,
            "scrape_course_info_for_course_code_with_sections",
            side_effect=scrape_course,
        ):
            with self.assertRaisesRegex(scraper.ScrapeError, "1 course worker"):
                scraper.scrape_all_courses_with_sections(
                    ["FAIL101", "CMSC131"], "202601"
                )

    def test_collection_failure_does_not_call_database(self):
        with patch.object(
            scraper,
            "collect_scraped_data",
            side_effect=scraper.ScrapeError("incomplete collection"),
        ), patch.object(scraper.dbmanager, "sync_scraped_data") as sync:
            with self.assertRaises(scraper.ScrapeError):
                scraper.run_scrape()

        sync.assert_not_called()

    def test_complete_collection_calls_database_sync_once(self):
        collected = ([('CMSC', 'Computer')], "202601", [{"course_code": "CMSC131"}])
        with patch.object(scraper, "collect_scraped_data", return_value=collected), patch.object(
            scraper.dbmanager, "sync_scraped_data"
        ) as sync:
            scraper.run_scrape()

        sync.assert_called_once_with(*collected)


if __name__ == "__main__":
    unittest.main()
