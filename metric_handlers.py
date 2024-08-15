import json
import time
import logging
from database import get_db
import hmac
from auth_handlers import BaseHandler
import hashlib

logger = logging.getLogger(__name__)

class MetricsHandler(BaseHandler):
    def initialize(self, metric_processor, secret_key):
        super().initialize()
        self.metric_processor = metric_processor
        self.secret_key = secret_key

    async def post(self):
        try:
            data = json.loads(self.request.body)
            signature = self.request.headers.get('X-Signature')

            if not signature:
                logger.warning("Metrics received without signature")
                self.set_status(400)
                self.write({"error": "Signature is required"})
                return

            if not self.verify_signature(data, signature):
                logger.warning("Invalid signature for metrics")
                self.set_status(400)
                self.write({"error": "Invalid signature"})
                return

            hostname = data['hostname']
            metrics = data['metrics']
            tags = data.get('tags', {})

            for metric_name, metric_data in metrics.items():
                if isinstance(metric_data, dict):
                    timestamp = metric_data.get('timestamp', time.time())
                    value = metric_data.get('value')
                    message = metric_data.get('message')
                else:
                    timestamp = time.time()
                    value = metric_data
                    message = None

                metric_item = {
                    'hostname': hostname,
                    'metric_name': metric_name,
                    'value': value,
                    'timestamp': timestamp,
                    'tags': tags,
                    'message': message
                }
                self.metric_processor.enqueue_metric(metric_item)

            self.write({"status": "received"})
        except Exception as e:
            logger.error(f"Error in MetricsHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

    def verify_signature(self, data, signature):
        message = json.dumps(data, sort_keys=True, separators=(',', ':'))
        expected_signature = hmac.new(self.secret_key.encode(), message.encode(), hashlib.sha256).hexdigest()
        return hmac.compare_digest(signature, expected_signature)


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

                metric_value = row['value']
                if isinstance(metric_value, str):
                    try:
                        metric_value = json.loads(metric_value)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in metric value for {hostname} - {row['metric_name']}")
                        metric_value = {'value': metric_value}  # Fallback to treating it as a single value
                elif not isinstance(metric_value, dict):
                    metric_value = {'value': metric_value}  # Wrap non-dict values

                latest_metrics[hostname]['metrics'][row['metric_name']] = metric_value

            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(latest_metrics))
        except Exception as e:
            logger.error(f"Error in FetchLatestHandler: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write(json.dumps({"error": "Internal server error", "details": str(e)}))


class FetchHistoryHandler(BaseHandler):
    async def get(self, hostname, metric_name):
        try:
            start = float(self.get_argument("start", 0))
            end = float(self.get_argument("end", time.time()))
            target_points = int(self.get_argument("target_points", 500))  # Changed from limit to target_points

            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT m.timestamp, m.value, m.message
                    FROM metrics m
                    JOIN hosts h ON m.host_id = h.id
                    WHERE h.hostname = %s AND m.metric_name = %s AND m.timestamp BETWEEN %s AND %s
                    ORDER BY m.timestamp
                """, (hostname, metric_name, start, end))

                history = cursor.fetchall()

            result = []
            for point in history:
                data_point = {'timestamp': point['timestamp']}
                value = point['value']

                if isinstance(value, str):
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        logger.error(f"Invalid JSON in metric value for {hostname} - {metric_name}")
                        value = {'value': value}  # Fallback to treating it as a single value
                elif not isinstance(value, dict):
                    value = {'value': value}  # Wrap non-dict values

                data_point.update(value)
                if point['message']:
                    data_point['message'] = point['message']
                result.append(data_point)

            # Adaptive sampling
            if len(result) > target_points:
                sampled_result = []
                step = len(result) / target_points
                current_index = 0
                while current_index < len(result):
                    sampled_result.append(result[int(current_index)])
                    current_index += step
                result = sampled_result

            self.write(json.dumps(result))
        except Exception as e:
            logger.error(f"Error in FetchHistoryHandler: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write({"error": "Internal server error", "details": str(e)})

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