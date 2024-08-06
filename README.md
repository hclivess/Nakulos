# Python Monitoring System

This is an advanced, scalable monitoring system built with Python and Tornado. It consists of a server that collects and stores metrics, and a client that gathers and sends metrics to the server.

## Features

- Server-client architecture for distributed monitoring
- Extensible metric collection through custom Python scripts
- PostgreSQL database for robust and scalable storage of metrics
- In-memory queue system for efficient metric processing
- Client-side buffering for resilience against network issues
- Advanced data aggregation for handling thousands of hosts
- RESTful API for fetching latest metrics and historical data
- Automatic cleanup and aggregation of old data
- Configurable alert system with support for downtimes
- Interactive dashboard with real-time updates
- URL-based host selection for easy sharing and bookmarking
- Host tagging system for better organization
- Admin interface for managing clients and uploading new metrics
- Data simulation tool for testing and development

## Requirements

- Python 3.7+
- Tornado web framework
- PostgreSQL database
- psycopg2-binary (PostgreSQL adapter for Python)
- Chart.js (for dashboard visualizations)

## Installation

1. Clone this repository or download the source files.
2. Install the required packages:
pip install tornado psycopg2-binary
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
- `client_config.json`: Configuration file for client settings
- `dashboard.html`: HTML template for the dashboard
- `dashboard.js`: JavaScript for dashboard functionality
- `chart.js`: Chart configuration for dashboard
- `alerts.js`: Alert management on the dashboard
- `downtimes.js`: Downtime management on the dashboard
- `utils.js`: Utility functions for the dashboard
- `admin_interface.html`: HTML template for the admin interface
- `admin.js`: JavaScript for admin interface functionality
- `simulator.py`: Data simulation tool for testing
- `wipeout.py`: Script to clear all data (use with caution)

## Setup

1. Server Setup:
- Create a `server_config.json` file with your database and server settings.
- Run the server using: `python server.py`

2. Client Setup:
- Create a metrics directory in the same location as client.py
- Add custom Python scripts to the metrics directory for each metric you want to collect
- Configure `client_config.json` with appropriate settings
- Run the client using: `python client.py`

## Usage

### Dashboard

Access the dashboard at `http://localhost:8888/dashboard`. Features include:
- Real-time metric visualizations
- Host selection with URL-based sharing
- Alert configuration and management
- Downtime scheduling

### Admin Interface

Access the admin interface at `http://localhost:8888/admin`. Features include:
- Client configuration management
- Metric script uploading
- Host tag management

### Adding Custom Metrics

To add a new metric:
1. Create a new Python file in the metrics directory
2. Implement a `collect()` function that returns the metric value

### Client Buffering

The client implements a local buffer to store metrics when the server is unreachable. Features include:
- Automatic buffering of metrics during network issues
- Configurable buffer size
- Automatic retry and buffer flush when connection is restored
- Persistent storage using SQLite for resilience against client restarts

### API Endpoints

- `GET /`: Check if the server is running
- `POST /metrics`: Submit metrics (used by the client)
- `GET /fetch/latest`: Get the latest metrics for all hosts
- `GET /fetch/history/<hostname>/<metric_name>`: Get historical data for a specific metric
- `GET /fetch/hosts`: Get a list of all hosts
- `POST /alert_config`: Configure alerts
- `POST /alert_state`: Update alert state
- `GET /downtime`: Get downtime information
- `POST /downtime`: Schedule a downtime
- `GET /fetch/recent_alerts`: Get recent alerts
- `POST /aggregate`: Trigger manual data aggregation
- `POST /remove_host`: Remove a host from the system
- `POST /update_tags`: Update tags for a host
- `GET /client_config`: Fetch client configuration
- `POST /client_config`: Register or update client configuration

## Data Simulation

Use `simulator.py` to generate test data:
python simulator.py
Follow the prompts to specify the number of hosts, days of data, and metrics per hour.

## Data Retention and Aggregation

The system uses advanced data aggregation techniques to efficiently store historical data. Aggregation is performed automatically on a schedule, and can also be triggered manually via the API.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0).

For more details about this license, please visit:
https://creativecommons.org/licenses/by-nc/4.0/