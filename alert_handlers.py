import json
import logging
from auth_handlers import BaseHandler

logger = logging.getLogger(__name__)

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

            self.write({"status": "success"})
        except Exception as e:
            logger.error(f"Error in AlertStateHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})

class RecentAlertsHandler(BaseHandler):
    async def get(self):
        try:
            hostname = self.get_argument('hostname', None)
            limit = int(self.get_argument('limit', 10))

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
                cursor.execute(query, params)
                recent_alerts = cursor.fetchall()

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

            self.write(json.dumps(result))
        except Exception as e:
            logger.error(f"Error in RecentAlertsHandler: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})