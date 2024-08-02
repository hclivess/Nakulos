import sqlite3
import random
import time
from datetime import datetime
import math

# Database connection
conn = sqlite3.connect('metrics.db')
cursor = conn.cursor()


def generate_test_data(num_hosts, days_of_data, metrics_per_hour):
    print("Generating test data...")
    hosts = [f"host_{i}" for i in range(num_hosts)]
    metrics = ['cpu_usage', 'memory_usage', 'disk_usage', 'network_in', 'network_out']

    end_time = time.time()
    start_time = end_time - (days_of_data * 24 * 60 * 60)

    def generate_value(metric, timestamp, base_value):
        hour = datetime.fromtimestamp(timestamp).hour
        day_progress = (hour / 24) * 2 * math.pi

        if metric == 'cpu_usage':
            # CPU usage fluctuates more during work hours
            return base_value + 20 * math.sin(day_progress) + random.uniform(-5, 5)
        elif metric == 'memory_usage':
            # Memory usage gradually increases and resets (e.g., due to restarts)
            return (base_value + (timestamp - start_time) / (3600 * 24)) % 100
        elif metric == 'disk_usage':
            # Disk usage slowly increases over time
            return min(base_value + (timestamp - start_time) / (3600 * 24 * 10), 100)
        elif metric in ['network_in', 'network_out']:
            # Network traffic has peaks during work hours
            return base_value + 30 * math.sin(day_progress) + random.uniform(-10, 10)

    total_data_points = num_hosts * len(metrics) * days_of_data * 24 * metrics_per_hour
    points_generated = 0

    for host in hosts:
        print(f"Generating data for {host}")
        base_values = {metric: random.uniform(20, 60) for metric in metrics}

        current_time = start_time
        while current_time < end_time:
            for metric in metrics:
                value = generate_value(metric, current_time, base_values[metric])
                value = max(0, min(value, 100))  # Ensure value is between 0 and 100

                cursor.execute('''
                    INSERT INTO metrics (hostname, metric_name, timestamp, value, additional_data)
                    VALUES (?, ?, ?, ?, ?)
                ''', (host, metric, current_time, value, '{"location": "Test Location"}'))

                points_generated += 1
                if points_generated % 10000 == 0:
                    print(f"Generated {points_generated}/{total_data_points} data points")

            current_time += 3600 / metrics_per_hour

    conn.commit()
    print("Data generation complete.")

def clear_test_data():
    print("Clearing existing test data...")
    cursor.execute("DELETE FROM metrics WHERE hostname LIKE 'host_%'")
    conn.commit()
    print("Test data cleared.")


if __name__ == "__main__":
    num_hosts = int(input("Enter the number of hosts to generate: "))
    days_of_data = int(input("Enter the number of days of data to generate: "))
    metrics_per_hour = int(input("Enter the number of metric entries per hour: "))

    clear_test_data()

    start_time = time.time()
    generate_test_data(num_hosts, days_of_data, metrics_per_hour)
    end_time = time.time()

    print(f"Data generation took {end_time - start_time:.2f} seconds.")

    # Close the database connection
    conn.close()