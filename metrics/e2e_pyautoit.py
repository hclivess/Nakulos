import autoit

def collect():
    try:
        # Move mouse to specific coordinates and click
        autoit.mouse_click("left", 100, 200)

        # Type some text
        autoit.send("Hello, World!")

        # Wait for a window to appear and activate it
        if not autoit.win_wait_active("Notepad", timeout=10):
            raise Exception("Notepad window did not appear")

        # Click a control in the window
        if not autoit.control_click("Notepad", "", "Edit1"):
            raise Exception("Failed to click Edit control in Notepad")

        return 1  # Success
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return 0  # Failure

if __name__ == "__main__":
    result = collect()
    print(f"Test result: {'Success' if result == 1 else 'Failure'}")