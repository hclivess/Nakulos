import random
import time
import math


def collect():
    metrics = {}

    # Simulate a primary metric with some variability
    try:
        primary_value = random.gauss(50, 15)
        metrics["primary"] = {
            "value": round(primary_value, 2)
        }
    except Exception as e:
        metrics["primary"] = {
            "value": None,
            "message": f"UnexpectedError: {str(e)}"
        }

    # Simulate a secondary metric that depends on the primary
    try:
        secondary_value = primary_value * random.uniform(0.8, 1.2)
        metrics["secondary"] = {
            "value": round(secondary_value, 2)
        }
    except Exception as e:
        metrics["secondary"] = {
            "value": None,
            "message": f"UnexpectedError: {str(e)}"
        }

    # Simulate a cyclic metric (e.g., simulating daily patterns)
    try:
        current_hour = time.localtime().tm_hour
        cyclic_value = 50 + 30 * math.sin(current_hour * math.pi / 12)
        metrics["cyclic"] = {
            "value": round(cyclic_value, 2)
        }
    except Exception as e:
        metrics["cyclic"] = {
            "value": None,
            "message": f"UnexpectedError: {str(e)}"
        }

    # Simulate an occasional spike
    try:
        if random.random() < 0.1:  # 10% chance of a spike
            spike_value = random.uniform(90, 100)
            metrics["spike"] = {
                "value": round(spike_value, 2)
            }
    except Exception as e:
        metrics["spike"] = {
            "value": None,
            "message": f"UnexpectedError: {str(e)}"
        }

    # Simulate an occasional error condition
    try:
        if random.random() < 0.05:  # 5% chance of an error
            raise Exception("Simulated error in data collection")
        metrics["error_prone"] = {
            "value": random.randint(1, 100)
        }
    except Exception as e:
        metrics["error_prone"] = {
            "value": None,
            "message": f"UnexpectedError: {str(e)}"
        }

    return metrics