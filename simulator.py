import psycopg2
import random
import time
from datetime import datetime
import math
import json
from multiprocessing import Pool, cpu_count
import io


def load_config():
    with open('server_config.json', 'r') as config_file:
        return json.load(config_file)


config = load_config()


def get_db_connection():
    db_config = config['database']
    return psycopg2.connect(
        host=db_config['host'],
        database=db_config['database_name'],
        user=db_config['username'],
        password=db_config['password'],
        port=db_config['port']
    )


def generate_host_data(args):
    host, days_of_data, metrics_per_hour, start_time, end_time = args
    metrics = ['cpu_usage', 'memory_usage', 'disk_usage', 'network_in', 'network_out']
    base_values = {metric: random.uniform(20, 60) for metric in metrics}

    data = []
    current_time = start_time
    while current_time < end_time:
        for metric in metrics:
            value = generate_value(metric, current_time, base_values[metric], start_time)
            value = max(0, min(value, 100))
            data.append(f"{host}\t{metric}\t{current_time}\t{value}")
        current_time += 3600 / metrics_per_hour

    return "\n".join(data)


def generate_value(metric, timestamp, base_value, start_time):
    hour = datetime.fromtimestamp(timestamp).hour
    day_progress = (hour / 24) * 2 * math.pi

    if metric == 'cpu_usage':
        return base_value + 20 * math.sin(day_progress) + random.uniform(-5, 5)
    elif metric == 'memory_usage':
        return (base_value + (timestamp - start_time) / (3600 * 24)) % 100
    elif metric == 'disk_usage':
        return min(base_value + (timestamp - start_time) / (3600 * 24 * 10), 100)
    elif metric in ['network_in', 'network_out']:
        return base_value + 30 * math.sin(day_progress) + random.uniform(-10, 10)


def generate_test_data(num_hosts, days_of_data, metrics_per_hour):
    print("Generating test data...")
    hosts = [f"host_{i}" for i in range(num_hosts)]
    end_time = time.time()
    start_time = end_time - (days_of_data * 24 * 60 * 60)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert hosts
    host_data = [(host, f"Alias for {host}", "Test Location") for host in hosts]
    cursor.executemany("INSERT INTO hosts (hostname, alias, location) VALUES (%s, %s, %s)", host_data)
    conn.commit()

    # Generate metric data in parallel
    with Pool(cpu_count()) as pool:
        results = pool.map(generate_host_data,
                           [(host, days_of_data, metrics_per_hour, start_time, end_time) for host in hosts])

    # Use COPY to insert metric data
    cursor.execute(
        "CREATE TEMPORARY TABLE temp_metrics (hostname TEXT, metric_name TEXT, timestamp FLOAT, value FLOAT)")
    for result in results:
        with io.StringIO(result) as f:
            cursor.copy_from(f, 'temp_metrics', columns=('hostname', 'metric_name', 'timestamp', 'value'))

    cursor.execute("""
        INSERT INTO metrics (host_id, metric_name, timestamp, value)
        SELECT h.id, tm.metric_name, tm.timestamp, tm.value
        FROM temp_metrics tm
        JOIN hosts h ON tm.hostname = h.hostname
    """)

    conn.commit()
    cursor.close()
    conn.close()
    print("Data generation complete.")


def clear_test_data():
    print("Clearing existing test data...")
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # First, delete related records in downtimes table
        cursor.execute("""
            DELETE FROM downtimes 
            WHERE host_id IN (SELECT id FROM hosts WHERE hostname LIKE 'host_%')
        """)

        # Then, delete related records in alerts table
        cursor.execute("""
            DELETE FROM alerts 
            WHERE host_id IN (SELECT id FROM hosts WHERE hostname LIKE 'host_%')
        """)

        # Now delete the metrics
        cursor.execute("""
            DELETE FROM metrics 
            WHERE host_id IN (SELECT id FROM hosts WHERE hostname LIKE 'host_%')
        """)

        # Finally, delete the hosts
        cursor.execute("DELETE FROM hosts WHERE hostname LIKE 'host_%'")

        conn.commit()
        print("Test data cleared successfully.")
    except Exception as e:
        conn.rollback()
        print(f"An error occurred while clearing test data: {e}")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    num_hosts = int(input("Enter the number of hosts to generate: "))
    days_of_data = int(input("Enter the number of days of data to generate: "))
    metrics_per_hour = int(input("Enter the number of metric entries per hour: "))

    clear_test_data()

    start_time = time.time()
    generate_test_data(num_hosts, days_of_data, metrics_per_hour)
    end_time = time.time()

    print(f"Data generation took {end_time - start_time:.2f} seconds.")