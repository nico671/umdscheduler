import requests
from bs4 import BeautifulSoup
from flask_restful import Resource

TESTUDO_HOME_URL = "https://app.testudo.umd.edu/soc/"


def _depts_fetcher():
    resp = requests.get(TESTUDO_HOME_URL)
    if resp.status_code != 200:
        raise Exception("Failed to fetch data from Testudo")
    soup = BeautifulSoup(resp.text, "html.parser")
    cols_wrapper = soup.select_one("#course-prefixes-page")
    all_depts = []
    for row in cols_wrapper.find_all("div", class_="course-prefix row"):
        dept_code = row.find(
            "span", class_="prefix-abbrev push_one two columns"
        ).text.strip()
        dept_name = row.find("span", class_="prefix-name nine columns").text.strip()
        all_depts.append({dept_code: dept_name})
    return all_depts


class Departments(Resource):
    def get(self):
        return _depts_fetcher()
