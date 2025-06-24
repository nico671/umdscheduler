from contextlib import contextmanager

from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@contextmanager
def get_driver():
    """Util that provides a WebDriver instance that automatically quits on exit."""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    try:
        yield driver  # Hands control back to the calling function
    finally:
        driver.quit()  # Ensures WebDriver is always closed
