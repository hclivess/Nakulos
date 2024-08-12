import autoit
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def collect():
    start_time = time.time()
    metrics = {
        'success': 0,
        'mouse_click_success': 0,
        'text_input_success': 0,
        'window_activation_success': 0,
        'control_click_success': 0,
        'execution_time': 0
    }

    try:
        # Move mouse to specific coordinates and click
        autoit.mouse_click("left", 100, 200)
        metrics['mouse_click_success'] = 1
        logging.info("Mouse clicked at coordinates: (100, 200)")

        # Type some text
        autoit.send("Hello, World!")
        metrics['text_input_success'] = 1
        logging.info("Text 'Hello, World!' sent")

        # Wait for a window to appear and activate it
        if autoit.win_wait_active("Notepad", timeout=10):
            metrics['window_activation_success'] = 1
            logging.info("Notepad window activated")
        else:
            logging.warning("Notepad window did not appear within timeout")

        # Click a control in the window
        if autoit.control_click("Notepad", "", "Edit1"):
            metrics['control_click_success'] = 1
            logging.info("Successfully clicked Edit control in Notepad")
        else:
            logging.warning("Failed to click Edit control in Notepad")

        metrics['success'] = 1
    except Exception as e:
        logging.error(f"An error occurred: {str(e)}")

    metrics['execution_time'] = time.time() - start_time
    return metrics

if __name__ == "__main__":
    result = collect()
    print(f"Test result: {'Success' if result['success'] == 1 else 'Failure'}")
    print(f"Mouse click success: {'Yes' if result['mouse_click_success'] == 1 else 'No'}")
    print(f"Text input success: {'Yes' if result['text_input_success'] == 1 else 'No'}")
    print(f"Window activation success: {'Yes' if result['window_activation_success'] == 1 else 'No'}")
    print(f"Control click success: {'Yes' if result['control_click_success'] == 1 else 'No'}")
    print(f"Execution time: {result['execution_time']:.2f} seconds")