from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

def collect():
    metrics = {}
    start_time = time.time()

    driver = None
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=chrome_options)

        # Measure page load time
        page_load_start = time.time()
        driver.get("https://example.com")
        page_load_time = time.time() - page_load_start
        metrics['page_load_time'] = {'value': page_load_time}

        # Measure element interaction time
        interaction_start = time.time()
        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "More information..."))
            )
            element.click()
            metrics['element_interaction_success'] = {'value': 1}
        except TimeoutException:
            metrics['element_interaction_success'] = {'value': 0, 'message': 'Element interaction timed out'}
        element_interaction_time = time.time() - interaction_start
        metrics['element_interaction_time'] = {'value': element_interaction_time}

        # Measure assertion time
        assertion_start = time.time()
        try:
            h1_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            if h1_element.text != "Example Domains":
                metrics['assertion_success'] = {'value': 0, 'message': 'Assertion failed'}
            else:
                metrics['assertion_success'] = {'value': 1}
        except (TimeoutException, NoSuchElementException):
            metrics['assertion_success'] = {'value': 0, 'message': 'Assertion timed out or element not found'}
        assertion_time = time.time() - assertion_start
        metrics['assertion_time'] = {'value': assertion_time}

        metrics['success'] = {'value': 1}

    except Exception as e:
        metrics['success'] = {'value': 0, 'message': f"UnexpectedError: {str(e)}"}
        metrics['page_load_time'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['element_interaction_success'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['element_interaction_time'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['assertion_success'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['assertion_time'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    finally:
        if driver:
            driver.quit()

    execution_time = time.time() - start_time
    metrics['execution_time'] = {'value': execution_time}

    return metrics

if __name__ == "__main__":
    result = collect()
    print(result)