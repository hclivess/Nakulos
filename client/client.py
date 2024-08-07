import asyncio
import logging
from config_manager import ConfigManager
from metric_collector import MetricCollector
from network_manager import NetworkManager
from buffer_manager import BufferManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MonitoringClient:
    def __init__(self):
        self.config_manager = ConfigManager()
        self.metric_collector = MetricCollector(self.config_manager)
        self.network_manager = NetworkManager(self.config_manager)
        self.buffer_manager = BufferManager(self.config_manager)

    async def run(self):
        while True:
            try:
                now = asyncio.get_event_loop().time()
                fraction_of_second = now % 1
                time_to_next_second = 1 - fraction_of_second

                await asyncio.sleep(time_to_next_second)

                start_time = asyncio.get_event_loop().time()

                await self.network_manager.check_for_updates()
                await self.network_manager.fetch_new_metrics()

                collected_metrics = self.metric_collector.collect_metrics()
                if collected_metrics:
                    data_to_send = {
                        "hostname": self.config_manager.hostname,
                        "client_id": self.config_manager.client_id,
                        "metrics": collected_metrics,
                        "tags": self.config_manager.tags
                    }
                    await self.network_manager.send_metrics(data_to_send)

                elapsed_time = asyncio.get_event_loop().time() - start_time
                sleep_time = min(self.metric_collector.get_shortest_interval(), 60) - elapsed_time
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
                else:
                    logger.warning(f"Metric collection took longer than shortest interval: {elapsed_time:.2f} seconds")
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                await asyncio.sleep(60)  # Wait for 1 minute before retrying

if __name__ == "__main__":
    client = MonitoringClient()
    try:
        asyncio.run(client.run())
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt. Shutting down...")
    finally:
        client.buffer_manager.close()
        logger.info("Client shut down successfully.")