import json
import logging
from auth_handlers import BaseHandler

logger = logging.getLogger(__name__)

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

            result = [
                {
                    "id": downtime['id'],
                    "hostname": downtime['hostname'],
                    "start_time": downtime['start_time'],
                    "end_time": downtime['end_time']
                } for downtime in downtimes
            ]
            self.write(json.dumps(result))
        except Exception as e:
            logger.error(f"Error in DowntimeHandler GET: {str(e)}", exc_info=True)
            self.set_status(500)
            self.write({"error": "Internal server error"})

    async def post(self):
        try:
            data = json.loads(self.request.body)

            if 'hostname' not in data:
                self.set_status(400)
                self.write({"error": "Hostname not provided"})
                return

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

            self.write({"status": "success", "id": downtime_id})

        except Exception as e:
            logger.error(f"Error in DowntimeHandler POST: {str(e)}", exc_info=True)
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

            self.write({"status": "success"})
        except Exception as e:
            logger.error(f"Error in DowntimeHandler DELETE: {str(e)}")
            self.set_status(500)
            self.write({"error": "Internal server error"})