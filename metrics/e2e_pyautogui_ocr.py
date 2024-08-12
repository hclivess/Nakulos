import pyautogui
import pytesseract
from PIL import Image
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def collect():
    start_time = time.time()
    try:
        # Move mouse to specific coordinates and click
        pyautogui.click(100, 200)
        logging.info("Clicked at coordinates: (100, 200)")

        # Take a screenshot
        screenshot = pyautogui.screenshot()

        # Perform OCR on the screenshot
        text = pytesseract.image_to_string(screenshot)
        char_count = len(text.strip())
        if char_count == 0:
            logging.warning("No text found in screenshot")
        else:
            logging.info(f"OCR Result: {text[:50]}...")  # Log first 50 characters

        # Find and click an image on screen
        location = pyautogui.locateOnScreen('button.png', confidence=0.8)
        if location:
            pyautogui.click(location)
            logging.info("Button 'button.png' found and clicked")
            button_found = 1
        else:
            logging.warning("Button image 'button.png' not found on screen")
            button_found = 0

        success = 1
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        success = 0
        char_count = 0
        button_found = 0

    execution_time = time.time() - start_time

    return {
        'success': success,
        'char_count': char_count,
        'button_found': button_found,
        'execution_time': execution_time
    }


if __name__ == "__main__":
    result = collect()
    print(f"Test result: {'Success' if result['success'] == 1 else 'Failure'}")
    print(f"OCR character count: {result['char_count']}")
    print(f"Button found: {'Yes' if result['button_found'] == 1 else 'No'}")
    print(f"Execution time: {result['execution_time']:.2f} seconds")