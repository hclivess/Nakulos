from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time

def collect():
    start_time = time.time()
    metrics = {
        'success': 0,
        'page_load_time': 0,
        'element_interaction_time': 0,
        'assertion_time': 0,
        'error_count': 0
    }

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
        metrics['page_load_time'] = time.time() - page_load_start

        # Measure element interaction time
        interaction_start = time.time()
        try:
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "More information..."))
            )
            element.click()
        except TimeoutException:
            metrics['error_count'] += 1
        metrics['element_interaction_time'] = time.time() - interaction_start

        # Measure assertion time
        assertion_start = time.time()
        try:
            h1_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
            if h1_element.text != "Example Domains":
                metrics['error_count'] += 1
        except (TimeoutException, NoSuchElementException):
            metrics['error_count'] += 1
        metrics['assertion_time'] = time.time() - assertion_start

        metrics['success'] = 1 if metrics['error_count'] == 0 else 0

    except Exception as e:
        print(f"An unexpected error occurred: {str(e)}")
        metrics['error_count'] += 1
        metrics['success'] = 0
    finally:
        if driver:
            driver.quit()

    metrics['execution_time'] = time.time() - start_time
    return metrics

if __name__ == "__main__":
    result = collect()
    print(f"Test result: {'Success' if result['success'] == 1 else 'Failure'}")
    print(f"Page load time: {result['page_load_time']:.2f} seconds")
    print(f"Element interaction time: {result['element_interaction_time']:.2f} seconds")
    print(f"Assertion time: {result['assertion_time']:.2f} seconds")
    print(f"Error count: {result['error_count']}")
    print(f"Total execution time: {result['execution_time']:.2f} seconds")