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

    def start(self):
        self.running = True
        for _ in range(self.num_workers):
            worker = threading.Thread(target=self._worker_loop)
            worker.start()
            self.workers.append(worker)
        logger.info(f"Started {self.num_workers} worker threads")

    def stop(self):
        self.running = False
        for worker in self.workers:
            worker.join()
        self.workers = []
        logger.info("All worker threads stopped")

    def enqueue(self, item):
        self.queue.put(item)

    def _worker_loop(self):
        while self.running:
            try:
                item = self.queue.get(timeout=1)
                self._process_item(item)
                self.queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing item: {e}")

    def _process_item(self, item):
        # This method should be overridden in a subclass
        raise NotImplementedError("_process_item must be implemented in a subclass")


class MetricProcessor(QueueManager):
    def __init__(self, num_workers=3):
        super().__init__(num_workers)
        self.db = get_db()

    def _process_item(self, item):
        hostname = item['hostname']
        metric_name = item['metric_name']
        value = item['value']
        timestamp = item['timestamp']

        with self.db.get_cursor() as cursor:
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

            for alert in alerts:
                if self._check_alert_condition(alert, value):
                    self._trigger_alert(alert, hostname, metric_name, value)

            self.db.conn.commit()

    def _check_alert_condition(self, alert, value):
        if alert['condition'] == 'above':
            return value > alert['threshold']
        elif alert['condition'] == 'below':
            return value < alert['threshold']
        return False

    def _trigger_alert(self, alert, hostname, metric_name, value):
        logger.info(f"Alert triggered for {hostname} - {metric_name}: {value}")
        # Implement alert notification logic here (e.g., send email, push notification)

        # Log the alert in the database
        with self.db.get_cursor() as cursor:
            cursor.execute(
                "INSERT INTO metrics (host_id, metric_name, timestamp, value) VALUES (%s, %s, %s, %s)",
                (alert['host_id'], 'alert_triggered', time.time(), f"{metric_name}:{value}")
            )
            self.db.conn.commit()