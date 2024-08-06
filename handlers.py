import tornado.web
import json
import time
import logging
from database import get_db
from data_aggregator import aggregate_data
import os

logger = logging.getLogger(__name__)


class AdminInterfaceHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("admin_interface.html")

class UpdateClientHandler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        client_id = data.get('client_id')
        config = data.get('config')

        if not client_id or not config:
            self.set_status(400)
            self.write({"message": "Both client_id and config are required"})
            return

        try:
            with get_db().get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO client_configs (client_id, config)
                    VALUES (%s, %s)
                    ON CONFLICT (client_id) DO UPDATE
                    SET config = EXCLUDED.config, last_updated = NOW()
                """, (client_id, json.dumps(config)))
            self.write({"message": "Client configuration updated successfully"})
        except Exception as e:
            logger.error(f"Error updating client configuration: {str(e)}")
            self.set_status(500)
            self.write({"message": "Internal server error"})


class UploadMetricHandler(tornado.web.RequestHandler):
    def post(self):
        data = json.loads(self.request.body)
        metric_name = data.get('name')
        metric_code = data.get('code')

        if not metric_name or not metric_code:
            self.set_status(400)
            self.write({"message": "Both name and code are required"})
            return

        try:
            metrics_dir = "./metrics"  # Adjust this path as needed
            os.makedirs(metrics_dir, exist_ok=True)

            file_path = os.path.join(metrics_dir, f"{metric_name}.py")
            with open(file_path, 'w') as f:
                f.write(metric_code)

            self.write({"message": f"Metric '{metric_name}' uploaded successfully"})
        except Exception as e:
            logger.error(f"Error uploading metric: {str(e)}")
            self.set_status(500)
            self.write({"message": "Internal server error"})

class BaseHandler(tornado.web.RequestHandler):
    def initialize(self):
        self.db = get_db()

class MainHandler(BaseHandler):
    def get(self):
        self.write("Monitoring Server is running")

class MetricsHandler(BaseHandler):
    def initialize(self, metric_processor):
        super().initialize()
        self.metric_processor = metric_processor

    async def post(self):
        try:
            data = json.loads(self.request.body)
            hostname = data['hostname']
            metrics = data['metrics']
            timestamp = time.time()
            tags = data.get('tags', {})

            for metric_name, value in metrics.items():
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

import json

class FetchLatestHandler(BaseHandler):
    async def get(self):
        try:
            with self.db.get_cursor() as cursor:
                try:
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
                except Exception as e:
                    logger.error(f"Database operation failed: {e}")
                    self.set_status(500)
                    self.write(json.dumps({"error": "Internal server error"}))
                    return

            latest_metrics = {}
            for row in results:
                hostname = row['hostname']
                if hostname not in latest_metrics:
                    latest_metrics[hostname] = {
                        'metrics': {},
                        'tags': row['tags'] if isinstance(row['tags'], dict) else {}
                    }
                latest_metrics[hostname]['metrics'][row['metric_name']] = float(row['value'])
                #latest_metrics[hostname]['metrics'][row['metric_name'] + '_timestamp'] = float(row['timestamp'])

            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(latest_metrics))
        except Exception as e:
            logger.error(f"Error in FetchLatestHandler: {str(e)}")
            self.set_status(500)
            self.write(json.dumps({"error": "Internal server error"}))

class ClientConfigHandler(BaseHandler):
    async def get(self):
        client_id = self.get_argument('client_id', None)
        if not client_id:
            self.set_status(400)
            self.write({"error": "Client ID is required"})
            return

        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT config, last_updated FROM client_configs WHERE client_id = %s", (client_id,))
                result = cursor.fetchone()

            if result:
                config, last_updated = result['config'], result['last_updated']
                self.write({
                    "status": "update_available" if str(last_updated) > self.get_argument('last_update', '0') else "no_update",
                    "config": config
                })
            else:
                self.set_status(404)
                self.write({"status": "unknown_client"})
        except Exception as e:
            logger.error(f"Error in ClientConfigHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

    async def post(self):
        data = json.loads(self.request.body)
        client_id = data.get('client_id')
        new_config = data.get('config')

        if not client_id or not new_config:
            self.set_status(400)
            self.write({"error": "Both client_id and config are required"})
            return

        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO client_configs (client_id, config)
                    VALUES (%s, %s)
                    ON CONFLICT (client_id) DO UPDATE
                    SET config = EXCLUDED.config, last_updated = NOW()
                """, (client_id, json.dumps(new_config)))

            self.write({"status": "success", "message": "Client registered successfully"})
        except Exception as e:
            logger.error(f"Error registering client: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

class FetchHistoryHandler(BaseHandler):
    async def get(self, hostname, metric_name):
        try:
            start = float(self.get_argument("start", 0))
            end = float(self.get_argument("end", time.time()))
            limit = int(self.get_argument("limit", 500))  # Default limit of 500 points

            logger.info(
                f"Fetching history for {hostname}, metric: {metric_name}, start: {start}, end: {end}, limit: {limit}")

            with self.db.get_cursor() as cursor:
                # Fetch all points, ordered by timestamp
                cursor.execute("""
                    SELECT m.timestamp, m.value
                    FROM metrics m
                    JOIN hosts h ON m.host_id = h.id
                    WHERE h.hostname = %s AND m.metric_name = %s AND m.timestamp BETWEEN %s AND %s
                    ORDER BY m.timestamp
                """, (hostname, metric_name, start, end))

                history = cursor.fetchall()

            total_points = len(history)

            # If we have more points than the limit, sample them
            if total_points > limit:
                step = max(1, total_points // limit)
                history = [history[i] for i in range(0, total_points, step)]
                history = history[:limit]  # Ensure we don't exceed the limit

            result = [[row['timestamp'], row['value']] for row in history]
            logger.info(f"Sending response with {len(result)} data points out of {total_points} total")
            self.write(json.dumps(result))
        except Exception as e:
            logger.error(f"Error in FetchHistoryHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

class FetchHostsHandler(BaseHandler):
    async def get(self):
        try:
            with self.db.get_cursor() as cursor:
                try:
                    cursor.execute("SELECT hostname, tags FROM hosts")
                    hosts = cursor.fetchall()
                except Exception as e:
                    logger.error(f"Database operation failed: {e}")
                    self.set_status(500)
                    self.write(json.dumps({"error": "Internal server error"}))
                    return

            result = {}
            for host in hosts:
                hostname = host['hostname']
                tags = host['tags'] if isinstance(host['tags'], dict) else {}
                result[hostname] = {"tags": tags}

            self.set_header("Content-Type", "application/json")
            self.write(json.dumps(result))
        except Exception as e:
            logger.error(f"Error in FetchHostsHandler: {str(e)}")
            self.set_status(500)
            self.write(json.dumps({"error": "Internal server error"}))

class AlertConfigHandler(BaseHandler):
    async def get(self):
        try:
            with self.db.get_cursor() as cursor:
                try:
                    cursor.execute("""
                        SELECT a.id, h.hostname, a.metric_name, a.condition, a.threshold, a.duration, a.enabled
                        FROM alerts a
                        JOIN hosts h ON a.host_id = h.id
                    """)
                    alerts = cursor.fetchall()
                except Exception as e:
                    logger.error(f"Database operation failed: {e}")
                    self.set_status(500)
                    self.write({"error": "Internal server error"})
                    return

            result = [dict(a) for a in alerts]
            self.write(json.dumps(result))
        except Exception as e:
            logger.error(f"Error in AlertConfigHandler GET: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

    async def post(self):
        try:
            data = json.loads(self.request.body)
            with self.db.get_cursor() as cursor:
                try:
                    cursor.execute("SELECT id FROM hosts WHERE hostname = %s", (data['hostname'],))
                    host = cursor.fetchone()
                    if not host:
                        self.set_status(404)
                        self.write({"error": "Host not found"})
                        return

                    cursor.execute("""
                        INSERT INTO alerts (host_id, metric_name, condition, threshold, duration, enabled)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING id
                    """, (host['id'], data['metric_name'], data['condition'], data['threshold'], data['duration'], True))
                    alert_id = cursor.fetchone()['id']
                except Exception as e:
                    logger.error(f"Database operation failed: {e}")
                    self.set_status(500)
                    self.write({"error": "Internal server error"})
                    return

            self.write({"status": "success", "id": alert_id})
        except Exception as e:
            logger.error(f"Error in AlertConfigHandler POST: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

    async def delete(self):
        try:
            data = json.loads(self.request.body)
            with self.db.get_cursor() as cursor:
                try:
                    cursor.execute("DELETE FROM alerts WHERE id = %s", (data['id'],))
                    if cursor.rowcount == 0:
                        self.set_status(404)
                        self.write({"error": "Alert not found"})
                        return
                except Exception as e:
                    logger.error(f"Database operation failed: {e}")
                    self.set_status(500)
                    self.write({"error": "Internal server error"})
                    return

            self.write({"status": "success"})
        except Exception as e:
            logger.error(f"Error in AlertConfigHandler DELETE: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

class AlertStateHandler(BaseHandler):
    async def post(self):
        try:
            data = json.loads(self.request.body)
            with self.db.get_cursor() as cursor:
                try:
                    cursor.execute("UPDATE alerts SET enabled = %s WHERE id = %s", (data['enabled'], data['id']))
                    if cursor.rowcount == 0:
                        self.set_status(404)
                        self.write({"error": "Alert not found"})
                        return
                except Exception as e:
                    logger.error(f"Database operation failed: {e}")
                    self.set_status(500)
                    self.write({"error": "Internal server error"})
                    return

            self.write({"status": "success"})
        except Exception as e:
            logger.error(f"Error in AlertStateHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

class DowntimeHandler(BaseHandler):
    async def get(self):
        try:
            hostname = self.get_argument('hostname', None)

            query = """
                SELECT d.id, h.hostname, d.start_time, d.end_time
                FROM downtimes d
                JOIN hosts h ON d.host_id = h.id
            """
            params = []

            if hostname and hostname != 'all':
                query += " WHERE h.hostname = %s"
                params.append(hostname)

            query += " ORDER BY d.start_time DESC"

            with self.db.get_cursor() as cursor:
                try:
                    cursor.execute(query, params)
                    downtimes = cursor.fetchall()
                    logger.info(f"Fetched {len(downtimes)} downtimes for hostname: {hostname}")
                except Exception as e:
                    logger.error(f"Database operation failed: {e}", exc_info=True)
                    self.set_status(500)
                    self.write({"error": "Internal server error"})
                    return

            result = [
                {
                    "id": downtime['id'],
                    "hostname": downtime['hostname'],
                    "start_time": downtime['start_time'],
                    "end_time": downtime['end_time']
                } for downtime in downtimes
            ]
            logger.info(f"Sending downtime data: {result}")
            self.write(json.dumps(result))
        except Exception as e:
            logger.error(f"Error in DowntimeHandler GET: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write({"error": "Internal server error"})

    async def post(self):
        try:
            data = json.loads(self.request.body)
            logger.info(f"Received downtime data: {data}")

            if 'hostname' not in data:
                logger.error("Hostname not provided in downtime data")
                self.set_status(400)
                self.write({"error": "Hostname not provided"})
                return

            with self.db.get_cursor() as cursor:
                try:
                    cursor.execute("SELECT id FROM hosts WHERE hostname = %s", (data['hostname'],))
                    host = cursor.fetchone()
                    if not host:
                        logger.error(f"Host not found: {data['hostname']}")
                        self.set_status(404)
                        self.write({"error": "Host not found"})
                        return

                    logger.info(f"Inserting downtime for host_id: {host['id']}")
                    cursor.execute("""
                        INSERT INTO downtimes (host_id, start_time, end_time)
                        VALUES (%s, %s, %s)
                        RETURNING id
                    """, (host['id'], data['start_time'], data['end_time']))
                    downtime_id = cursor.fetchone()['id']
                    logger.info(f"Downtime inserted with id: {downtime_id}")
                except Exception as e:
                    logger.error(f"Database operation failed: {e}", exc_info=True)
                    self.set_status(500)
                    self.write({"error": "Internal server error"})
                    return

            self.write({"status": "success", "id": downtime_id})

        except Exception as e:
            logger.error(f"Error in DowntimeHandler POST: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write({"error": "Internal server error"})

    async def delete(self):
        try:
            data = json.loads(self.request.body)
            with self.db.get_cursor() as cursor:
                try:
                    cursor.execute("DELETE FROM downtimes WHERE id = %s", (data['id'],))
                    if cursor.rowcount == 0:
                        self.set_status(404)
                        self.write({"error": "Downtime not found"})
                        return
                except Exception as e:
                    logger.error(f"Database operation failed: {e}")
                    self.set_status(500)
                    self.write({"error": "Internal server error"})
                    return

            self.write({"status": "success"})
        except Exception as e:
            logger.error(f"Error in DowntimeHandler DELETE: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

class RecentAlertsHandler(BaseHandler):
    async def get(self):
        try:
            hostname = self.get_argument('hostname', None)
            limit = int(self.get_argument('limit', 10))

            logger.info(f"Fetching recent alerts for hostname: {hostname}, limit: {limit}")

            query = """
                SELECT ah.id, h.hostname, a.metric_name, ah.timestamp, ah.value, 
                       a.condition, a.threshold
                FROM alert_history ah
                JOIN alerts a ON ah.alert_id = a.id
                JOIN hosts h ON ah.host_id = h.id
            """
            params = []

            if hostname and hostname != 'all':
                query += " WHERE h.hostname = %s"
                params.append(hostname)

            query += " ORDER BY ah.timestamp DESC LIMIT %s"
            params.append(limit)

            with self.db.get_cursor() as cursor:
                try:
                    cursor.execute(query, params)
                    recent_alerts = cursor.fetchall()
                    logger.info(f"Fetched {len(recent_alerts)} recent alerts")
                except Exception as e:
                    logger.error(f"Database operation failed: {e}")
                    self.set_status(500)
                    self.write({"error": "Internal server error"})
                    return

            result = [
                {
                    "id": alert['id'],
                    "hostname": alert['hostname'],
                    "metric_name": alert['metric_name'],
                    "timestamp": alert['timestamp'],
                    "value": alert['value'],
                    "condition": alert['condition'],
                    "threshold": alert['threshold']
                } for alert in recent_alerts
            ]

            logger.info(f"Sending response with {len(result)} alerts")
            self.write(json.dumps(result))
        except Exception as e:
            logger.error(f"Error in RecentAlertsHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

class DashboardHandler(BaseHandler):
    def get(self):
        try:
            with open("dashboard.html", "r") as file:
                self.write(file.read())
        except Exception as e:
            logger.error(f"Error in DashboardHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

class JSHandler(BaseHandler):
    def initialize(self, filename):
        super().initialize()
        self.filename = filename

    def get(self):
        try:
            with open(self.filename, "r") as file:
                self.set_header("Content-Type", "application/javascript")
                self.write(file.read())
        except Exception as e:
            logger.error(f"Error in JSHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

class AggregateDataHandler(BaseHandler):
    def get(self):
        try:
            aggregate_data()
            self.write({"status": "Data aggregation triggered successfully"})
        except Exception as e:
            logger.error(f"Error in AggregateDataHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})


class RemoveHostHandler(BaseHandler):
        async def post(self):
            try:
                data = json.loads(self.request.body)
                hostname = data.get('hostname')

                if not hostname:
                    self.set_status(400)
                    self.write(json.dumps({"error": "Hostname is required"}))
                    return

                with self.db.get_cursor() as cursor:
                    cursor.execute("BEGIN")
                    try:
                        cursor.execute("DELETE FROM hosts WHERE hostname = %s", (hostname,))
                        if cursor.rowcount == 0:
                            cursor.execute("ROLLBACK")
                            self.set_status(404)
                            self.write(json.dumps({"error": "Host not found"}))
                        else:
                            cursor.execute("COMMIT")
                            self.write(
                                json.dumps({"status": "success", "message": f"Host {hostname} removed successfully"}))
                    except Exception as e:
                        cursor.execute("ROLLBACK")
                        raise e

            except Exception as e:
                logger.error(f"Error in RemoveHostHandler: {str(e)}")
                self.set_status(500)
                self.write(json.dumps({"error": "Internal server error"}))