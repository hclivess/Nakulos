import pyautogui
import pytesseract
from PIL import Image

def collect():
    try:
        # Move mouse to specific coordinates and click
        pyautogui.click(100, 200)

        # Take a screenshot
        screenshot = pyautogui.screenshot()

        # Perform OCR on the screenshot
        text = pytesseract.image_to_string(screenshot)
        if not text:
            raise Exception("No text found in screenshot")

        # Find and click an image on screen
        location = pyautogui.locateOnScreen('button.png')
        if location:
            pyautogui.click(location)
        else:
            raise Exception("Button image not found on screen")

        return 1  # Success
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return 0  # Failure

if __name__ == "__main__":
    result = collect()
    print(f"Test result: {'Success' if result == 1 else 'Failure'}")