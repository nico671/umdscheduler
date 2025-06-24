import requests
from bs4 import BeautifulSoup
from flask_restful import Resource

TESTUDO_HOME_URL = "https://app.testudo.umd.edu/soc/"


def _semester_fetcher():
    resp = requests.get(TESTUDO_HOME_URL)
    if resp.status_code != 200:
        raise Exception("Failed to fetch data from Testudo")
    soup = BeautifulSoup(resp.text, "html.parser")
    semester_selecter = soup.find("select", {"id": "term-id-input"})
    all_available_semesters = []
    for option in semester_selecter.find_all("option"):
        all_available_semesters.append(
            {
                "code": option["value"],
                "name": option.text.strip(),
            }
        )
    return all_available_semesters


class Semesters(Resource):
    def get(self):
        return _semester_fetcher()
