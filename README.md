# Python Monitoring System

This is an advanced, scalable monitoring system built with Python and Tornado. It consists of a server that collects and stores metrics, and a client that gathers and sends metrics to the server.

## Features

- Server-client architecture for distributed monitoring
- Extensible metric collection through custom Python scripts
- PostgreSQL database for robust and scalable storage of metrics
- In-memory queue system for efficient metric processing
- Advanced data aggregation for handling thousands of hosts
- RESTful API for fetching latest metrics and historical data
- Automatic cleanup and aggregation of old data
- Configurable alert system with support for downtimes

## Requirements

- Python 3.7+
- Tornado web framework
- PostgreSQL database
- psycopg2-binary (PostgreSQL adapter for Python)

## Installation

1. Clone this repository or download the source files.
2. Install the required packages:
pip install tornado psycopg2-binary
Copy
3. Ensure you have PostgreSQL installed and running.

## File Structure

- `server.py`: The main server script
- `client.py`: The client script for collecting and sending metrics
- `metrics/`: Directory for custom metric collection scripts
- `handlers.py`: Contains all the request handlers
- `database.py`: Database connection and operations
- `queue_manager.py`: Manages the in-memory queue for metric processing
- `data_aggregator.py`: Handles data aggregation for efficient storage
- `server_config.json`: Configuration file for server settings

## Setup

1. Server Setup:
- Create a `server_config.json` file with your database and server settings:
  ```json
  {
    "database": {
      "host": "localhost",
      "port": 5432,
      "username": "your_username",
      "password": "your_password",
      "database_name": "monitoring"
    },
    "webapp": {
      "port": 8888
    }
  }
  ```
- Run the server using:
  ```
  python server.py
  ```
- The server will start on http://localhost:8888 (or the port specified in your config)

2. Client Setup:
- Create a metrics directory in the same location as client.py
- Add custom Python scripts to the metrics directory for each metric you want to collect
- Each script should have a collect() function that returns the metric value
- Run the client using:
  ```
  python client.py
  ```

## Usage

### Adding Custom Metrics

To add a new metric:
1. Create a new Python file in the metrics directory
2. Implement a collect() function that returns the metric value
3. The client will automatically load and use this new metric

## Example (metrics/cpu_usage.py):

python
import psutil

def collect():
 return psutil.cpu_percent()

## API Endpoints

GET /: Check if the server is running
POST /metrics: Submit metrics (used by the client)
GET /fetch/latest: Get the latest metrics for all hosts
GET /fetch/history/<hostname>/<metric_name>: Get historical data for a specific metric
GET /fetch/hosts: Get a list of all hosts
POST /alert_config: Configure alerts
POST /alert_state: Update alert state
GET /downtime: Get downtime information
POST /downtime: Schedule a downtime
GET /fetch/recent_alerts: Get recent alerts
POST /aggregate: Trigger manual data aggregation

## Fetching Data
To fetch the latest metrics:
Copycurl http://localhost:8888/fetch/latest
To fetch historical data:
Copycurl http://localhost:8888/fetch/history/hostname/metric_name?limit=100

## Configuration

Server configuration: Edit the server_config.json file
Client configuration: Edit the config dictionary in client.py

Data Retention and Aggregation
The system now uses advanced data aggregation techniques to efficiently store historical data. This allows for handling thousands of hosts while maintaining performance. Aggregation is performed automatically on a schedule, and can also be triggered manually via the API.

## Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0).

This means you are free to:

- Share — copy and redistribute the material in any medium or format
- Adapt — remix, transform, and build upon the material

Under the following terms:

- Attribution — You must give appropriate credit, provide a link to the license, and indicate if changes were made. You may do so in any reasonable manner, but not in any way that suggests the licensor endorses you or your use.
- NonCommercial — You may not use the material for commercial purposes.

For commercial use, please contact the project maintainers to discuss licensing options.

For more details about this license, please visit:
https://creativecommons.org/licenses/by-nc/4.0/
This license allows free use for non-commercial purposes while requiring attribution. It also leaves the door open for potential commercial licensing arrangements.