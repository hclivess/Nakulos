import uuid
import socket
import tornado.ioloop
import tornado.httpclient
import json
import importlib.util
import os
import time
import logging
import datetime
import asyncio
import sys

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


class MonitoringClient:
    def __init__(self):
        self.config = self.load_config()
        self.server_url = self.config['server_url']
        self.interval = self.config['interval']
        self.metrics_modules = self.load_metric_modules()
        self.metrics_store = MetricsStore()
        self.hostname = socket.gethostname()
        self.client_id = self.config.get('client_id', self.hostname)
        self.tags = self.config.get('tags', {})
        self.last_update = self.config.get('last_update', '0')
        logger.info(f"MonitoringClient initialized with config: {self.config}")

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

        # Reload the module if it's already loaded
        if metric_name in sys.modules:
            spec = importlib.util.spec_from_file_location(metric_name, file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            sys.modules[metric_name] = module
            self.metrics_modules[metric_name] = module

    def load_config(self):
        try:
            with open('client_config.json', 'r') as config_file:
                config = json.load(config_file)
                logger.info(f"Loaded config: {config}")

                # Check if client_id is not defined or empty
                if not config.get('client_id'):
                    # Generate a new client_id using UUID
                    new_client_id = str(uuid.uuid4())
                    config['client_id'] = new_client_id

                    # Save the updated config with the new client_id
                    self.save_config(config)

                    logger.info(f"Generated new client_id: {new_client_id}")

                return config
        except FileNotFoundError:
            logger.error("Config file not found. Using default configuration.")
            default_config = {
                "server_url": "http://localhost:8888",
                "interval": 60,
                "metrics_dir": "./metrics",
                "client_id": str(uuid.uuid4()),  # Generate a new client_id
                "last_update": "0"
            }
            self.save_config(default_config)
            return default_config
        except json.JSONDecodeError:
            logger.error("Invalid JSON in config file. Using default configuration.")
            default_config = {
                "server_url": "http://localhost:8888",
                "interval": 60,
                "metrics_dir": "./metrics",
                "client_id": str(uuid.uuid4()),  # Generate a new client_id
                "last_update": "0"
            }
            self.save_config(default_config)
            return default_config

    def save_config(self, config):
        with open('client_config.json', 'w') as config_file:
            json.dump(config, config_file, indent=4)
        logger.info("Saved new configuration to client_config.json")

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

    def collect_metrics(self):
        for name, module in self.metrics_modules.items():
            try:
                value = module.collect()
                self.metrics_store.add_metric(name, value)
                logger.info(f"Collected metric {name}: {value}")
            except Exception as e:
                logger.error(f"Error collecting metric {name}: {e}", exc_info=True)
        return self.metrics_store.get_all_latest()

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
                    "interval": self.interval,
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
        # Preserve important fields
        preserved_fields = ['client_id', 'server_url']
        for field in preserved_fields:
            if field not in new_config and field in self.config:
                new_config[field] = self.config[field]

        # Update the configuration
        self.config.update(new_config)

        # Apply the updated configuration
        self.interval = self.config.get('interval', 60)
        self.metrics_dir = self.config.get('metrics_dir', './metrics')
        self.tags = self.config.get('tags', {})
        self.last_update = self.config.get('last_update', str(int(time.time())))

        # Reload metric modules if metrics_dir has changed
        if self.metrics_dir != self.config.get('metrics_dir'):
            self.metrics_modules = self.load_metric_modules()

        self.save_config(new_config)
        logger.info("Applied new configuration")

    async def run(self):
        while True:
            now = time.time()
            fraction_of_second = now % 1
            time_to_next_second = 1 - fraction_of_second

            await asyncio.sleep(time_to_next_second)

            start_time = time.time()

            # Check for updates before sending metrics
            await self.check_for_updates()
            await self.fetch_new_metrics()
            await self.send_metrics_once()

            elapsed_time = time.time() - start_time
            sleep_time = self.interval - elapsed_time
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
            else:
                logger.warning(f"Metric collection took longer than interval: {elapsed_time:.2f} seconds")

    async def send_metrics_once(self):
        self.collect_metrics()
        latest_metrics = self.metrics_store.get_all_latest()
        metrics_to_send = {name: point.value for name, point in latest_metrics.items() if point is not None}
        data_to_send = {
            "hostname": self.hostname,
            "client_id": self.client_id,
            "metrics": metrics_to_send,
            "tags": self.tags
        }
        logger.info(f"Preparing to send metrics: {data_to_send}")
        try:
            client = tornado.httpclient.AsyncHTTPClient()
            response = await client.fetch(
                self.server_url + "/metrics",
                method="POST",
                body=json.dumps(data_to_send)
            )
            response_body = response.body.decode('utf-8')
            response_json = json.loads(response_body)
            logger.info(f"Sent metrics: {data_to_send}, response: {response_json}")
        except Exception as e:
            logger.error(f"Error sending metrics: {e}", exc_info=True)


if __name__ == "__main__":
    client = MonitoringClient()
    tornado.ioloop.IOLoop.current().run_sync(client.run)