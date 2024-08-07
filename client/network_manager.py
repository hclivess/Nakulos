import aiohttp
import json
import logging
import time
import asyncio

logger = logging.getLogger(__name__)

class NetworkManager:
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.max_retries = 5
        self.retry_delay = 5  # seconds

    async def send_metrics(self, data_to_send):
        for attempt in range(self.max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        f"{self.config_manager.server_url}/metrics",
                        json=data_to_send,
                        timeout=10.0
                    ) as response:
                        response_json = await response.json()
                        logger.info(f"Sent metrics: {data_to_send}, response: {response_json}")
                        return  # Exit the retry loop if successful
            except Exception as e:
                logger.error(f"Error sending metrics (attempt {attempt + 1}/{self.max_retries}): {e}", exc_info=True)
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                else:
                    # If all retries fail, add to buffer
                    self.config_manager.buffer_manager.add(data_to_send)
                    logger.info("Added metrics to buffer after failed retries")

    async def check_for_updates(self):
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.config_manager.server_url}/client_config?client_id={self.config_manager.client_id}&last_update={self.config_manager.last_update}"
                logger.info(f"Checking for updates at: {url}")
                async with session.get(url) as response:
                    if response.status == 200:
                        response_data = await response.json()
                        status = response_data.get('status')

                        if status == 'update_available':
                            new_config = response_data.get('config')
                            logger.info("New configuration received")
                            self.config_manager.update_config(new_config)
                            new_last_update = str(int(time.time()))
                            logger.info(f"Updating last_update from {self.config_manager.last_update} to {new_last_update}")
                            self.config_manager.set_last_update(new_last_update)
                        elif status == 'no_update':
                            logger.info("No new updates available")
                        else:
                            logger.warning(f"Unexpected status: {status}")
                    elif response.status == 404:
                        logger.warning("This client is not recognized by the server. Attempting to register.")
                        await self.register_client()
                    else:
                        logger.error(f"Failed to fetch updates. Status code: {response.status}")
        except Exception as e:
            logger.error(f"Error checking for updates: {e}", exc_info=True)

    async def register_client(self):
        try:
            async with aiohttp.ClientSession() as session:
                initial_config = {
                    "client_id": self.config_manager.client_id,
                    "config": {
                        "default_interval": self.config_manager.default_interval,
                        "metrics_dir": self.config_manager.metrics_dir,
                        "tags": self.config_manager.tags
                    }
                }
                async with session.post(
                    f"{self.config_manager.server_url}/client_config",
                    json=initial_config
                ) as response:
                    if response.status == 200:
                        logger.info("Client registered successfully")
                    else:
                        logger.error(f"Failed to register client. Status code: {response.status}")
        except Exception as e:
            logger.error(f"Error registering client: {e}", exc_info=True)

    async def fetch_new_metrics(self):
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.config_manager.server_url}/fetch_metrics?client_id={self.config_manager.client_id}"
                async with session.get(url) as response:
                    if response.status == 200:
                        new_metrics = await response.json()
                        for metric_name, metric_code in new_metrics.items():
                            self.config_manager.metric_collector.update_metric_script(metric_name, metric_code)
                    else:
                        logger.error(f"Failed to fetch new metrics. Status code: {response.status}")
        except Exception as e:
            logger.error(f"Error fetching new metrics: {e}")