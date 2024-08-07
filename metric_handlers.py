import json
import time
import logging
from database import get_db
from auth_handlers import BaseHandler

logger = logging.getLogger(__name__)

class MetricsHandler(BaseHandler):
    def initialize(self, metric_processor):
        super().initialize()
        self.metric_processor = metric_processor

    async def post(self):
        try:
            data = json.loads(self.request.body)
            hostname = data['hostname']
            metrics = data['metrics']
            tags = data.get('tags', {})

            for metric_name, metric_data in metrics.items():
                if isinstance(metric_data, dict) and 'value' in metric_data and 'timestamp' in metric_data:
                    value = metric_data['value']
                    timestamp = metric_data['timestamp']
                else:
                    value = metric_data
                    timestamp = time.time()

                metric_data = {
                    'hostname': hostname,
                    'metric_name': metric_name,
                    'value': value,
                    'timestamp': timestamp,
                    'tags': tags
                }
                self.metric_processor.enqueue_metric(metric_data)

            self.write({"status": "received"})
        except Exception as e:
            logger.error(f"Error in MetricsHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

class FetchLatestHandler(BaseHandler):
    async def get(self):
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT h.hostname, m.metric_name, m.timestamp, m.value, h.tags
                    FROM metrics m
                    JOIN hosts h ON m.host_id = h.id
                    WHERE (h.id, m.metric_name, m.timestamp) IN (
                        SELECT host_id, metric_name, MAX(timestamp)
                        FROM metrics
                        GROUP BY host_id, metric_name
                    )
                    ORDER BY h.hostname, m.metric_name
                """)
                results = cursor.fetchall()

            latest_metrics = {}
            for row in results:
                hostname = row['hostname']
                if hostname not in latest_metrics:
                    latest_metrics[hostname] = {
                        'metrics': {},
                        'tags': row['tags'] if isinstance(row['tags'], dict) else {}
                    }
                latest_metrics[hostname]['metrics'][row['metric_name']] = float(row['value'])

            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(latest_metrics))
        except Exception as e:
            logger.error(f"Error in FetchLatestHandler: {str(e)}")
            self.set_status(500)
            self.write(json.dumps({"error": "Internal server error"}))

class FetchHistoryHandler(BaseHandler):
    async def get(self, hostname, metric_name):
        try:
            start = float(self.get_argument("start", 0))
            end = float(self.get_argument("end", time.time()))
            limit = int(self.get_argument("limit", 500))

            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT m.timestamp, m.value
                    FROM metrics m
                    JOIN hosts h ON m.host_id = h.id
                    WHERE h.hostname = %s AND m.metric_name = %s AND m.timestamp BETWEEN %s AND %s
                    ORDER BY m.timestamp
                """, (hostname, metric_name, start, end))

                history = cursor.fetchall()

            result = []
            current_time = start
            for point in history:
                while current_time < point['timestamp']:
                    result.append([current_time, None])
                    current_time += 60
                result.append([point['timestamp'], point['value']])
                current_time = point['timestamp'] + 60

            while current_time <= end:
                result.append([current_time, None])
                current_time += 60

            total_points = len(result)

            if total_points > limit:
                step = max(1, total_points // limit)
                result = [result[i] for i in range(0, total_points, step)]
                result = result[:limit]

            self.write(json.dumps(result))
        except Exception as e:
            logger.error(f"Error in FetchHistoryHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

class FetchMetricsForHostHandler(BaseHandler):
    async def get(self):
        hostname = self.get_argument('hostname', None)
        if not hostname:
            self.set_status(400)
            self.write({"error": "Hostname is required"})
            return

        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT DISTINCT m.metric_name
                    FROM metrics m
                    JOIN hosts h ON m.host_id = h.id
                    WHERE h.hostname = %s
                    ORDER BY m.metric_name
                """, (hostname,))
                metrics = [row['metric_name'] for row in cursor.fetchall()]

            self.write(json.dumps(metrics))
        except Exception as e:
            logger.error(f"Error in FetchMetricsForHostHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

class DeleteMetricsHandler(BaseHandler):
    async def post(self):
        try:
            data = json.loads(self.request.body)
            hostname = data.get('hostname')
            metric_name = data.get('metric_name')
            start_time = data.get('start_time')
            end_time = data.get('end_time')

            if not hostname:
                self.set_status(400)
                self.write({"error": "Hostname is required"})
                return

            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT id FROM hosts WHERE hostname = %s", (hostname,))
                host = cursor.fetchone()
                if not host:
                    self.set_status(404)
                    self.write({"error": "Host not found"})
                    return

                host_id = host['id']

                delete_query = "DELETE FROM metrics WHERE host_id = %s"
                params = [host_id]

                if metric_name and metric_name != 'all':
                    delete_query += " AND metric_name = %s"
                    params.append(metric_name)

                if start_time:
                    delete_query += " AND timestamp >= %s"
                    params.append(start_time)
                if end_time:
                    delete_query += " AND timestamp <= %s"
                    params.append(end_time)

                cursor.execute(delete_query, params)
                deleted_count = cursor.rowcount

            message = f"Successfully deleted {deleted_count} metrics"
            if metric_name and metric_name != 'all':
                message += f" for {metric_name}"
            message += f" from host {hostname}"
            self.write({"message": message})
        except Exception as e:
            logger.error(f"Error in DeleteMetricsHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})