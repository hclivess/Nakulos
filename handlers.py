import tornado.web
import json
import time
import logging
from database import get_db
from data_aggregator import aggregate_data

logger = logging.getLogger(__name__)


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

            for metric_name, value in metrics.items():
                self.metric_processor.enqueue({
                    'hostname': hostname,
                    'metric_name': metric_name,
                    'value': value,
                    'timestamp': timestamp
                })

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
                    SELECT h.hostname, m.metric_name, m.timestamp, m.value, h.alias, h.location
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
                        'additional_data': {'alias': row['alias'], 'location': row['location']}
                    }
                latest_metrics[hostname]['metrics'][row['metric_name']] = row['value']

            self.write(json.dumps(latest_metrics))
        except Exception as e:
            logger.error(f"Error in FetchLatestHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})


class FetchHistoryHandler(BaseHandler):
    async def get(self, hostname, metric_name):
        try:
            start = float(self.get_argument("start", 0))
            end = float(self.get_argument("end", time.time()))
            limit = int(self.get_argument("limit", 1000))

            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT timestamp, value
                    FROM metrics m
                    JOIN hosts h ON m.host_id = h.id
                    WHERE h.hostname = %s AND m.metric_name = %s AND m.timestamp BETWEEN %s AND %s
                    ORDER BY m.timestamp DESC
                    LIMIT %s
                """, (hostname, metric_name, start, end, limit))
                history = cursor.fetchall()

            result = [[row['timestamp'], row['value']] for row in history]
            self.write(json.dumps(result))
        except Exception as e:
            logger.error(f"Error in FetchHistoryHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})


class FetchHostsHandler(BaseHandler):
    async def get(self):
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT hostname, alias, location FROM hosts")
                hosts = cursor.fetchall()

            result = [{"hostname": h['hostname'], "additional_data": {"alias": h['alias'], "location": h['location']}}
                      for h in hosts]
            self.write(json.dumps(result))
        except Exception as e:
            logger.error(f"Error in FetchHostsHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})


class AlertConfigHandler(BaseHandler):
    async def get(self):
        try:
            with self.db.get_cursor() as cursor:
                cursor.execute("""
                    SELECT a.id, h.hostname, a.metric_name, a.condition, a.threshold, a.duration, a.enabled
                    FROM alerts a
                    JOIN hosts h ON a.host_id = h.id
                """)
                alerts = cursor.fetchall()

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
                self.db.conn.commit()

            self.write({"status": "success", "id": alert_id})
        except Exception as e:
            logger.error(f"Error in AlertConfigHandler POST: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

    async def delete(self):
        try:
            data = json.loads(self.request.body)
            with self.db.get_cursor() as cursor:
                cursor.execute("DELETE FROM alerts WHERE id = %s", (data['id'],))
                if cursor.rowcount == 0:
                    self.set_status(404)
                    self.write({"error": "Alert not found"})
                    return
                self.db.conn.commit()

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
                cursor.execute("UPDATE alerts SET enabled = %s WHERE id = %s", (data['enabled'], data['id']))
                if cursor.rowcount == 0:
                    self.set_status(404)
                    self.write({"error": "Alert not found"})
                    return
                self.db.conn.commit()

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
                cursor.execute(query, params)
                downtimes = cursor.fetchall()

            result = [dict(d) for d in downtimes]
            self.write(json.dumps(result))
        except Exception as e:
            logger.error(f"Error in DowntimeHandler GET: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

    async def post(self):
        try:
            data = json.loads(self.request.body)
            with self.db.get_cursor() as cursor:
                cursor.execute("SELECT id FROM hosts WHERE hostname = %s", (data['hostname'],))
                host = cursor.fetchone()
                if not host:
                    self.set_status(404)
                    self.write({"error": "Host not found"})
                    return

                cursor.execute("""
                    INSERT INTO downtimes (host_id, start_time, end_time)
                    VALUES (%s, %s, %s)
                    RETURNING id
                """, (host['id'], data['start_time'], data['end_time']))
                downtime_id = cursor.fetchone()['id']
                self.db.conn.commit()

            self.write({"status": "success", "id": downtime_id})
        except Exception as e:
            logger.error(f"Error in DowntimeHandler POST: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

    async def delete(self):
        try:
            data = json.loads(self.request.body)
            with self.db.get_cursor() as cursor:
                cursor.execute("DELETE FROM downtimes WHERE id = %s", (data['id'],))
                if cursor.rowcount == 0:
                    self.set_status(404)
                    self.write({"error": "Downtime not found"})
                    return
                self.db.conn.commit()

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

            query = """
                SELECT h.hostname, m.timestamp, m.value as alert_details
                FROM metrics m
                JOIN hosts h ON m.host_id = h.id
                WHERE m.metric_name = 'alert_triggered'
            """
            params = []

            if hostname and hostname != 'all':
                query += " AND h.hostname = %s"
                params.append(hostname)

            query += " ORDER BY m.timestamp DESC LIMIT %s"
            params.append(limit)

            with self.db.get_cursor() as cursor:
                cursor.execute(query, params)
                recent_alerts = cursor.fetchall()

            result = [
                {
                    "hostname": alert['hostname'],
                    "timestamp": alert['timestamp'],
                    "alert_details": alert['alert_details']
                } for alert in recent_alerts
            ]
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