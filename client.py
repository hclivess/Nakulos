import uuid
import socket
import tornado.ioloop
import tornado.httpclient
import json
import importlib.util
import os
import time
import logging
import asyncio
import sys
import sqlite3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MetricPoint:
    def __init__(self, value, timestamp=None):
        self.value = value
        self.timestamp = timestamp or time.time()


class Metric:
    def __init__(self, name):
        self.name = name
        self.data_points = []

    def add_point(self, value):
        self.data_points.append(MetricPoint(value))

    def get_latest(self):
        return self.data_points[-1] if self.data_points else None


class MetricsStore:
    def __init__(self):
        self.metrics = {}

    def add_metric(self, name, value):
        if name not in self.metrics:
            self.metrics[name] = Metric(name)
        self.metrics[name].add_point(value)

    def get_metric(self, name):
        return self.metrics.get(name)

    def get_all_latest(self):
        return {name: metric.get_latest() for name, metric in self.metrics.items()}


class MetricBuffer:
    def __init__(self, buffer_size=1000, db_path='metric_buffer.db'):
        self.buffer_size = buffer_size
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    timestamp REAL NOT NULL
                )
            ''')

    def add(self, data):
        with self.conn:
            self.conn.execute('INSERT INTO metrics (data, timestamp) VALUES (?, ?)',
                              (json.dumps(data), time.time()))
        self.trim_buffer()

    def get_all(self):
        with self.conn:
            cursor = self.conn.execute('SELECT id, data, timestamp FROM metrics ORDER BY timestamp')
            return cursor.fetchall()

    def remove(self, ids):
        with self.conn:
            self.conn.executemany('DELETE FROM metrics WHERE id = ?', [(id,) for id in ids])

    def trim_buffer(self):
        with self.conn:
            count = self.conn.execute('SELECT COUNT(*) FROM metrics').fetchone()[0]
            if count > self.buffer_size:
                excess = count - self.buffer_size
                self.conn.execute(
                    f'DELETE FROM metrics WHERE id IN (SELECT id FROM metrics ORDER BY timestamp LIMIT {excess})')

    def close(self):
        self.conn.close()


class MonitoringClient:
    def __init__(self):
        self.config = self.load_config()
        self.server_url = self.config['server_url']
        self.default_interval = self.config.get('default_interval', 60)
        self.metric_intervals = self.config.get('metric_intervals', {})
        self.metrics_modules = self.load_metric_modules()
        self.metrics_store = MetricsStore()
        self.hostname = socket.gethostname()
        self.client_id = self.config.get('client_id', self.hostname)
        self.tags = self.config.get('tags', {})
        self.last_update = self.config.get('last_update', '0')
        self.metric_buffer = MetricBuffer()
        self.max_retries = 5
        self.retry_delay = 5  # seconds
        self.last_collection_times = {}
        logger.info(f"MonitoringClient initialized with config: {self.config}")

    def load_config(self):
        try:
            with open('client_config.json', 'r') as config_file:
                config = json.load(config_file)
                logger.info(f"Loaded config: {config}")

                if not config.get('client_id'):
                    new_client_id = str(uuid.uuid4())
                    config['client_id'] = new_client_id
                    self.save_config(config)
                    logger.info(f"Generated new client_id: {new_client_id}")

                return config
        except FileNotFoundError:
            logger.error("Config file not found. Using default configuration.")
            default_config = {
                "server_url": "http://localhost:8888",
                "default_interval": 60,
                "metrics_dir": "./metrics",
                "client_id": str(uuid.uuid4()),
                "last_update": "0"
            }
            self.save_config(default_config)
            return default_config
        except json.JSONDecodeError:
            logger.error("Invalid JSON in config file. Using default configuration.")
            default_config = {
                "server_url": "http://localhost:8888",
                "default_interval": 60,
                "metrics_dir": "./metrics",
                "client_id": str(uuid.uuid4()),
                "last_update": "0"
            }
            self.save_config(default_config)
            return default_config

    def save_config(self, config):
        config['last_update'] = self.last_update
        with open('client_config.json', 'w') as config_file:
            json.dump(config, config_file, indent=4)
        logger.info(f"Saved new configuration to client_config.json with last_update: {self.last_update}")

    def load_metric_modules(self):
        modules = {}
        for filename in os.listdir(self.config['metrics_dir']):
            if filename.endswith('.py'):
                module_name = filename[:-3]
                module_path = os.path.join(self.config['metrics_dir'], filename)
                try:
                    spec = importlib.util.spec_from_file_location(module_name, module_path)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    if hasattr(module, 'collect'):
                        modules[module_name] = module
                        logger.info(f"Loaded metric module: {module_name}")
                    else:
                        logger.warning(f"Metric module {module_name} does not have a 'collect' function")
                except Exception as e:
                    logger.error(f"Error loading metric module {module_name}: {str(e)}")
        return modules

    def get_metric_interval(self, metric_name):
        return self.metric_intervals.get(metric_name, self.default_interval)

    def collect_metrics(self):
        current_time = time.time()
        collected_metrics = {}
        for name, module in self.metrics_modules.items():
            interval = self.get_metric_interval(name)
            last_collection = self.last_collection_times.get(name, 0)
            if current_time - last_collection >= interval:
                try:
                    value = module.collect()
                    self.metrics_store.add_metric(name, value)
                    collected_metrics[name] = value
                    self.last_collection_times[name] = current_time
                    logger.info(f"Collected metric {name}: {value}")
                except Exception as e:
                    logger.error(f"Error collecting metric {name}: {e}", exc_info=True)
        return collected_metrics

    async def check_for_updates(self):
        try:
            client = tornado.httpclient.AsyncHTTPClient()
            url = f"{self.server_url}/client_config?client_id={self.client_id}&last_update={self.last_update}"
            logger.info(f"Checking for updates at: {url}")
            response = await client.fetch(url, method="GET", raise_error=False)

            if response.code == 200:
                response_data = json.loads(response.body)
                status = response_data.get('status')

                if status == 'update_available':
                    new_config = response_data.get('config')
                    logger.info("New configuration received")
                    self.apply_new_config(new_config)
                    # Update last_update only when a new config is actually received and applied
                    new_last_update = str(int(time.time()))
                    logger.info(f"Updating last_update from {self.last_update} to {new_last_update}")
                    self.last_update = new_last_update
                    self.save_config(self.config)
                elif status == 'no_update':
                    logger.info("No new updates available")
                else:
                    logger.warning(f"Unexpected status: {status}")
            elif response.code == 404:
                logger.warning("This client is not recognized by the server. Attempting to register.")
                await self.register_client()
            else:
                logger.error(f"Failed to fetch updates. Status code: {response.code}")
        except Exception as e:
            logger.error(f"Error checking for updates: {e}", exc_info=True)

    async def register_client(self):
        try:
            client = tornado.httpclient.AsyncHTTPClient()
            initial_config = {
                "client_id": self.client_id,
                "config": {
                    "default_interval": self.default_interval,
                    "metrics_dir": self.config['metrics_dir'],
                    "tags": self.tags
                }
            }
            response = await client.fetch(
                f"{self.server_url}/client_config",
                method="POST",
                body=json.dumps(initial_config),
                headers={'Content-Type': 'application/json'}
            )
            if response.code == 200:
                logger.info("Client registered successfully")
            else:
                logger.error(f"Failed to register client. Status code: {response.code}")
        except Exception as e:
            logger.error(f"Error registering client: {e}", exc_info=True)

    def apply_new_config(self, new_config):
        preserved_fields = ['client_id', 'server_url']
        for field in preserved_fields:
            if field not in new_config and field in self.config:
                new_config[field] = self.config[field]

        self.config.update(new_config)

        self.default_interval = self.config.get('default_interval', 60)
        self.metric_intervals = self.config.get('metric_intervals', {})
        self.metrics_dir = self.config.get('metrics_dir', './metrics')
        self.tags = self.config.get('tags', {})

        if self.metrics_dir != self.config.get('metrics_dir'):
            self.metrics_modules = self.load_metric_modules()

        self.save_config(self.config)
        logger.info("Applied new configuration")

    async def fetch_new_metrics(self):
        try:
            client = tornado.httpclient.AsyncHTTPClient()
            url = f"{self.server_url}/fetch_metrics?client_id={self.client_id}"
            response = await client.fetch(url, method="GET")

            if response.code == 200:
                new_metrics = json.loads(response.body)
                for metric_name, metric_code in new_metrics.items():
                    self.update_metric_script(metric_name, metric_code)
            else:
                logger.error(f"Failed to fetch new metrics. Status code: {response.code}")
        except Exception as e:
            logger.error(f"Error fetching new metrics: {e}")

    def update_metric_script(self, metric_name, metric_code):
        file_path = os.path.join(self.config['metrics_dir'], f"{metric_name}.py")
        with open(file_path, 'w') as f:
            f.write(metric_code)

        if metric_name in sys.modules:
            spec = importlib.util.spec_from_file_location(metric_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[metric_name] = module
            self.metrics_modules[metric_name] = module

    async def send_metrics(self, data_to_send):
        for attempt in range(self.max_retries):
            try:
                client = tornado.httpclient.AsyncHTTPClient()
                response = await client.fetch(
                    self.server_url + "/metrics",
                    method="POST",
                    body=json.dumps(data_to_send),
                    request_timeout=10.0
                )
                response_body = response.body.decode('utf-8')
                response_json = json.loads(response_body)
                logger.info(f"Sent metrics: {data_to_send}, response: {response_json}")

                # If successful, try to send any buffered metrics
                await self.send_buffered_metrics()
                return  # Exit the retry loop if successful
            except Exception as e:
                logger.error(f"Error sending metrics (attempt {attempt + 1}/{self.max_retries}): {e}", exc_info=True)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    # If all retries fail, add to buffer
                    self.metric_buffer.add(data_to_send)
                    logger.info("Added metrics to buffer after failed retries")

    async def send_buffered_metrics(self):
        buffered_metrics = self.metric_buffer.get_all()
        successful_ids = []
        client = tornado.httpclient.AsyncHTTPClient()
        for id, data, _ in buffered_metrics:
            try:
                response = await client.fetch(
                    self.server_url + "/metrics",
                    method="POST",
                    body=data,
                    request_timeout=10.0
                )
                if response.code == 200:
                    successful_ids.append(id)
            except Exception as e:
                logger.error(f"Error sending buffered metric {id}: {e}", exc_info=True)
                break  # Stop trying to send if we encounter an error

        # Remove successfully sent metrics from the buffer
        if successful_ids:
            self.metric_buffer.remove(successful_ids)

    async def run(self):
        while True:
            try:
                now = time.time()
                fraction_of_second = now % 1
                time_to_next_second = 1 - fraction_of_second

                await asyncio.sleep(time_to_next_second)

                start_time = time.time()

                # Check for updates before sending metrics
                await self.check_for_updates()
                await self.fetch_new_metrics()

                collected_metrics = self.collect_metrics()
                if collected_metrics:
                    data_to_send = {
                        "hostname": self.hostname,
                        "client_id": self.client_id,
                        "metrics": {name: {'value': value, 'timestamp': time.time()} for name, value in collected_metrics.items()},
                        "tags": self.tags
                    }
                    await self.send_metrics(data_to_send)

                elapsed_time = time.time() - start_time
                sleep_time = min(self.get_metric_interval(metric) for metric in self.metrics_modules.keys()) - elapsed_time
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                else:
                    logger.warning(f"Metric collection took longer than shortest interval: {elapsed_time:.2f} seconds")
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(min(self.get_metric_interval(metric) for metric in self.metrics_modules.keys()))

if __name__ == "__main__":
    client = MonitoringClient()
    try:
        tornado.ioloop.IOLoop.current().run_sync(client.run)
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    finally:
        client.metric_buffer.close()
        logger.info("Client shut down successfully.")