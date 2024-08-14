import autoit
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def collect():
    metrics = {}
    start_time = time.time()

    try:
        # Move mouse to specific coordinates and click
        autoit.mouse_click("left", 100, 200)
        metrics['mouse_click_success'] = {'value': 1}
        logging.info("Mouse clicked at coordinates: (100, 200)")

        # Type some text
        autoit.send("Hello, World!")
        metrics['text_input_success'] = {'value': 1}
        logging.info("Text 'Hello, World!' sent")

        # Wait for a window to appear and activate it
        if autoit.win_wait_active("Notepad", timeout=10):
            metrics['window_activation_success'] = {'value': 1}
            logging.info("Notepad window activated")
        else:
            metrics['window_activation_success'] = {'value': 0, 'message': "Notepad window did not appear within timeout"}
            logging.warning("Notepad window did not appear within timeout")

        # Click a control in the window
        if autoit.control_click("Notepad", "", "Edit1"):
            metrics['control_click_success'] = {'value': 1}
            logging.info("Successfully clicked Edit control in Notepad")
        else:
            metrics['control_click_success'] = {'value': 0, 'message': "Failed to click Edit control in Notepad"}
            logging.warning("Failed to click Edit control in Notepad")

        metrics['success'] = {'value': 1}

    except Exception as e:
        metrics['success'] = {'value': 0, 'message': f"UnexpectedError: {str(e)}"}
        metrics['mouse_click_success'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['text_input_success'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['window_activation_success'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        metrics['control_click_success'] = {'value': None, 'message': f"UnexpectedError: {str(e)}"}
        logging.error(f"An error occurred: {str(e)}")

    execution_time = time.time() - start_time
    metrics['execution_time'] = {'value': execution_time}

    return metrics

if __name__ == "__main__":
    result = collect()
    print(result)