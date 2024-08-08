import json
import logging
import uuid
import socket
import time

logger = logging.getLogger(__name__)


class ConfigManager:
    def __init__(self, config_file='client_config.json'):
        self.config_file = config_file
        self.config = self.load_config()
        self.hostname = socket.gethostname()
        self.secret_key = self.config['secret_key']

        if not self.config.get('client_id'):
            self.config['client_id'] = str(uuid.uuid4())
            self.save_config(self.config)

        self.client_id = self.config['client_id']
        self.server_url = self.config['server_url']
        self.default_interval = self.config.get('default_interval', 60)
        self.metric_intervals = self.config.get('metric_intervals', {})
        self.metrics_dir = self.config.get('metrics_dir', './metrics')
        self.tags = self.config.get('tags', {})
        self.last_update = self.config.get('last_update', '0')

    def load_config(self):
        try:
            with open(self.config_file, 'r') as config_file:
                config = json.load(config_file)
                logger.info(f"Loaded config: {config}")
                return config
        except FileNotFoundError:
            logger.error("Config file not found. Using default configuration.")
            return self.get_default_config()
        except json.JSONDecodeError:
            logger.error("Invalid JSON in config file. Using default configuration.")
            return self.get_default_config()

    def get_default_config(self):
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
        if hasattr(self, 'last_update'):
            config['last_update'] = self.last_update
        with open(self.config_file, 'w') as config_file:
            json.dump(config, config_file, indent=4)
        logger.info(f"Saved new configuration to {self.config_file}")

    def update_config(self, new_config):
        self.config.update(new_config)
        self.client_id = self.config['client_id']
        self.hostname = self.config.get('hostname', socket.gethostname())
        self.default_interval = self.config.get('default_interval', 60)
        self.metric_intervals = self.config.get('metric_intervals', {})
        self.metrics_dir = self.config.get('metrics_dir', './metrics')
        self.tags = self.config.get('tags', {})
        self.last_update = self.config.get('last_update', self.last_update)
        self.save_config(self.config)
        ad
    def set_last_update(self, timestamp):
        self.last_update = str(int(timestamp))
        self.save_config(self.config)