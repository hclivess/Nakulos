Python Monitoring System

This is a simple, extensible monitoring system built with Python and Tornado. It consists of a server that collects and stores metrics, and a client that gathers and sends metrics to the server.

Features

- Server-client architecture for distributed monitoring
- Extensible metric collection through custom Python scripts
- SQLite database for persistent storage of metrics
- RESTful API for fetching latest metrics and historical data
- Automatic cleanup of old data

Requirements

- Python 3.7+
- Tornado web framework

Installation

1. Clone this repository or download the source files.
2. Install the required packages:

   pip install tornado

3. Ensure you have SQLite installed (it comes pre-installed with Python).

File Structure

- server.py: The main server script
- client.py: The client script for collecting and sending metrics
- metrics/: Directory for custom metric collection scripts

Setup

1. Server Setup:
   - Run the server using:
     python server.py
   - The server will start on http://localhost:8888
   - A metrics.db file will be created to store the metrics

2. Client Setup:
   - Create a metrics directory in the same location as client.py
   - Add custom Python scripts to the metrics directory for each metric you want to collect
   - Each script should have a collect() function that returns the metric value
   - Run the client using:
     python client.py

Usage

Adding Custom Metrics

To add a new metric:
1. Create a new Python file in the metrics directory
2. Implement a collect() function that returns the metric value
3. The client will automatically load and use this new metric

Example (metrics/cpu_usage.py):

import psutil

def collect():
    return psutil.cpu_percent()

API Endpoints

- GET /: Check if the server is running
- POST /metrics: Submit metrics (used by the client)
- GET /fetch/latest: Get the latest metrics for all hosts
- GET /fetch/history/<hostname>/<metric_name>: Get historical data for a specific metric
- GET /fetch/hosts: Get a list of all hosts

Fetching Data

To fetch the latest metrics:
curl http://localhost:8888/fetch/latest

To fetch historical data:
curl http://localhost:8888/fetch/history/hostname/metric_name?limit=100

Configuration

- Server configuration: Edit the variables at the top of server.py
- Client configuration: Edit the config dictionary in client.py

Data Retention

By default, the server keeps 30 days of data. You can modify this in the clean_old_data() function in server.py.

Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

License

This project is open source and available under the MIT License.