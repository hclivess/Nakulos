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
        self.additional_data = self.config.get('additional_data', {})
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
                "start_time": "00:00:00"
            }
        except json.JSONDecodeError:
            logger.error("Invalid JSON in config file. Using default configuration.")
            return {
                "server_url": "http://localhost:8888",
                "interval": 60,
                "metrics_dir": "./metrics",
                "start_time": "00:00:00"
            }

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

    async def run(self):
        while True:
            # Calculate the next run time
            now = time.time()
            fraction_of_second = now % 1
            time_to_next_second = 1 - fraction_of_second

            # Wait until the start of the next second
            await asyncio.sleep(time_to_next_second)

            # Collect and send metrics
            start_time = time.time()
            await self.send_metrics_once()

            # Calculate sleep time for the next interval
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
            "metrics": metrics_to_send,
            "additional_data": self.additional_data
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