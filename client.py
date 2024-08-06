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

    def load_config(self):
        try:
            with open('client_config.json', 'r') as config_file:
                config = json.load(config_file)
                logger.info(f"Loaded config: {config}")
                return config
        except FileNotFoundError:
            logger.error("Config file not found. Using default configuration.")
            return {
                "server_url": "http://localhost:8888",
                "interval": 60,
                "metrics_dir": "./metrics",
                "client_id": socket.gethostname(),
                "last_update": "0"
            }
        except json.JSONDecodeError:
            logger.error("Invalid JSON in config file. Using default configuration.")
            return {
                "server_url": "http://localhost:8888",
                "interval": 60,
                "metrics_dir": "./metrics",
                "client_id": socket.gethostname(),
                "last_update": "0"
            }

    def save_config(self):
        with open('client_config.json', 'w') as config_file:
            json.dump(self.config, config_file, indent=4)
        logger.info("Saved new configuration to client_config.json")

    def load_metric_modules(self):
        modules = {}
        for filename in os.listdir(self.config['metrics_dir']):
            if filename.endswith('.py'):
                module_name = filename[:-3]
                module_path = os.path.join(self.config['metrics_dir'], filename)
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                if hasattr(module, 'collect'):
                    modules[module_name] = module
                    logger.info(f"Loaded metric module: {module_name}")
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
        self.config = new_config
        self.config['last_update'] = str(int(time.time()))
        self.save_config()
        self.server_url = self.config['server_url']
        self.interval = self.config['interval']
        self.tags = self.config.get('tags', {})
        self.metrics_modules = self.load_metric_modules()
        self.last_update = self.config['last_update']
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