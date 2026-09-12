import subprocess
import sys
import unittest
from pathlib import Path


class ScraperImportTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
