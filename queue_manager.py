# queue_manager.py

import queue
import threading
import time
import logging
from database import get_db

logger = logging.getLogger(__name__)


class QueueManager:
    def __init__(self, num_workers=3):
        self.queue = queue.Queue()
        self.num_workers = num_workers
        self.workers = []
        self.running = False
        logger.info(f"QueueManager initialized with {num_workers} workers")

    def start(self):
        self.running = True
        for i in range(self.num_workers):
            worker = threading.Thread(target=self._worker_loop)
            worker.start()
            self.workers.append(worker)
        logger.info(f"Started {self.num_workers} worker threads")

    def stop(self):
        logger.info("Stopping QueueManager")
        self.running = False
        for worker in self.workers:
            worker.join()
        self.workers = []
        logger.info("All worker threads stopped")

    def enqueue(self, item):
        logger.debug(f"Enqueueing item: {item}")
        self.queue.put(item)

    def _worker_loop(self):
        logger.info("Worker loop started")
        while self.running:
            try:
                item = self.queue.get(timeout=1)
                logger.debug(f"Got item from queue: {item}")
                self._process_item(item)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing item: {e}", exc_info=True)

    def _process_item(self, item):
        raise NotImplementedError("_process_item must be implemented in a subclass")


class MetricProcessor(QueueManager):
    def __init__(self, num_workers=3):
        super().__init__(num_workers)
        self.db = get_db()
        logger.info("MetricProcessor initialized")

    def enqueue_metric(self, metric_data):
        self.queue.put(metric_data)

    def _process_item(self, item):
        hostname = item['hostname']
        metric_name = item['metric_name']
        value = item['value']
        timestamp = item['timestamp']
        additional_data = item.get('additional_data', {}) #todo

        logger.info(f"Processing metric: {hostname} - {metric_name}: {value}")

        with self.db.get_cursor() as cursor:
            try:
                # Get or create host
                cursor.execute("SELECT id FROM hosts WHERE hostname = %s", (hostname,))
                host = cursor.fetchone()
                if not host:
                    cursor.execute("INSERT INTO hosts (hostname) VALUES (%s) RETURNING id", (hostname,))
                    host = cursor.fetchone()

                host_id = host['id']

                # Insert metric
                cursor.execute(
                    "INSERT INTO metrics (host_id, metric_name, timestamp, value) VALUES (%s, %s, %s, %s)",
                    (host_id, metric_name, timestamp, value)
                )

                # Check alerts
                cursor.execute(
                    "SELECT * FROM alerts WHERE host_id = %s AND metric_name = %s AND enabled = TRUE",
                    (host_id, metric_name)
                )
                alerts = cursor.fetchall()

                logger.info(f"Checking {len(alerts)} alerts for {hostname} - {metric_name}")

                for alert in alerts:
                    logger.info(
                        f"Checking alert: {alert['id']} - Condition: {alert['condition']}, Threshold: {alert['threshold']}")
                    if self._check_alert_condition(alert, value):
                        self._trigger_alert(cursor, alert, hostname, metric_name, value, timestamp)
                    else:
                        logger.info(f"Alert condition not met for alert {alert['id']}")

                self.db.conn.commit()
            except Exception as e:
                logger.error(f"Error processing metric: {e}", exc_info=True)
                self.db.conn.rollback()

    def _check_alert_condition(self, alert, value):
        if alert['condition'] == 'above':
            return value > alert['threshold']
        elif alert['condition'] == 'below':
            return value < alert['threshold']
        return False

    def _trigger_alert(self, cursor, alert, hostname, metric_name, value, timestamp):
        logger.info(f"Alert triggered for {hostname} - {metric_name}: {value}")

        try:
            cursor.execute(
                "INSERT INTO alert_history (host_id, alert_id, timestamp, value) VALUES (%s, %s, %s, %s)",
                (alert['host_id'], alert['id'], timestamp, value)
            )
            logger.info(
                f"Alert logged to database: alert_id={alert['id']}, host_id={alert['host_id']}, timestamp={timestamp}, value={value}")
        except Exception as e:
            logger.error(f"Failed to log alert to database: {e}", exc_info=True)
