from bs4 import BeautifulSoup
from flask_restful import Resource
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from common.utils import get_driver

UMD_MAJORS_URL = "https://admissions.umd.edu/programs"


def _major_fetcher():
    with get_driver() as driver:
        # Load the UMD majors page
        driver.get(UMD_MAJORS_URL)

        # Wait for the page to load and the majors list to be present
        blah = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located(
                (
                    By.CSS_SELECTOR,
                    "#main > div > umd-lock > div > div.layout-content-columns > div.results",
                )
            )
        )

        major_list_wrapper_html = blah.get_attribute("outerHTML")
    soup = BeautifulSoup(major_list_wrapper_html, "html.parser")
    entry_list = soup.find_all("div", class_="list")
    assert len(entry_list) == 21, "Expected 21 entries, but found: {}".format(
        len(entry_list)
    )
    all_majors = []
    for entry in entry_list:
        for child_div in entry.children:
            major_name = child_div.find("h3").text.strip()
            major_link = child_div.find("a")["href"]
            major_info_list = []
            for info in child_div.find("div", class_="types").find_all("span"):
                major_info_list.append(info.text.strip())
            major_description = child_div.find("p").text.strip()
            all_majors.append(
                {
                    major_name: {
                        "link": major_link,
                        "info": major_info_list,
                        "description": major_description,
                    }
                }
            )
    return all_majors


class Majors(Resource):
    def get(self):
        return _major_fetcher()
