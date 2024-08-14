import pyautogui
import pytesseract
from PIL import Image
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def collect():
    metrics = {}
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

        metrics['char_count'] = {'value': char_count}

        # Find and click an image on screen
        location = pyautogui.locateOnScreen('button.png', confidence=0.8)
        if location:
            pyautogui.click(location)
            logging.info("Button 'button.png' found and clicked")
            metrics['button_found'] = {'value': 1}
        else:
            logging.warning("Button image 'button.png' not found on screen")
            metrics['button_found'] = {'value': 0}

        metrics['success'] = {'value': 1}

    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")
        metrics['success'] = {'value': 0, 'message': f"UnexpectedError: {str(e)}"}
        metrics['char_count'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['button_found'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}

    execution_time = time.time() - start_time
    metrics['execution_time'] = {'value': execution_time}

    return metrics

if __name__ == "__main__":
    result = collect()
    print(result)